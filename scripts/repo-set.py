#!/usr/bin/env python3
"""Repository-set helper for multi-repository /spec-run runs.

A multi-repository project keeps one shared knowledge base (`.ai/`, the specification,
task state) in a root directory that is not a git repository, and its code in git
repositories that are direct children of that root. This helper gives /spec-run the
deterministic, read-only facts it needs to run one shared plan as one independent
branch stack per repository.

Commands (each prints exactly one JSON object on stdout):
  mode       --root DIR [--repo NAME=BASE ...] [--state FILE]
             Classify the project: single-repository (the root is inside a git work
             tree; the ordinary single-repository rules apply unchanged) or
             multi-repository (the root is not; a repository set is required).
  preflight  --root DIR [--repo NAME=BASE ...] [--state FILE] [--branch NAME=BRANCH ...]
             [--allow-pr]
             Run the git preflight separately for every participating repository.
  route      --root DIR --plan FILE [--state FILE] [--repo NAME=BASE ...]
             Route every plan leaf to one repository, build the shared topological order,
             one stack per repository and the cross-repository dependency list, and name
             the earliest unfinished leaf.
  reconcile  --root DIR --state FILE [--repo NAME=BASE ...]
             Compare every recorded git checkpoint with its repository.

The repository set comes from --repo flags or, when they are omitted, from the task
state's `## Repositories` section; when both are present they must be identical.
NAME is the directory name of a git repository directly under the root; BASE is its
local base branch.

Contract: never writes a file, never changes a ref, index or working tree, and never
contacts a remote. Git runs with GIT_OPTIONAL_LOCKS=0 and without inherited GIT_*
variables. `gh auth status` runs only with --allow-pr.

Exit codes: 0 every check passed; 1 at least one check failed (the caller stops);
2 invalid invocation or unreadable input. Requires Python 3.9+ and git.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA_VERSION = 1
GIT_TIMEOUT_SECONDS = 30
NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
LEAF_ID = r"T-[0-9]{2,}[a-z]?(?:-fix-[a-z0-9]+(?:-[a-z0-9]+)*)?"
LEAF_ID_PATTERN = re.compile(rf"^{LEAF_ID}$")
REPOSITORY_LINE = re.compile(r"^- repo: (\S+) \| base_branch: (\S+)\s*$")
BLOCK_HEADER = re.compile(rf"^(\[composite\] )?({LEAF_ID}) \|")
BLOCK_FIELD = re.compile(r"^  ([a-z_]+):[ \t]?(.*?)\s*$")
WORKING_DIR = re.compile(r"^\s*-\s*working_dir:\s*(.*?)\s*$", re.M)
SHA_ENTRY = re.compile(r"(?:^|,)\s*([0-9a-f]{7,64})\b")
OPERATION_MARKERS = ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "BISECT_LOG",
                     "rebase-merge", "rebase-apply")
EMPTY_CELLS = {"", "-", "—", "–", "none", "n/a"}


class UsageError(Exception):
    def __init__(self, check: str, reason: str):
        super().__init__(reason)
        self.check = check
        self.reason = reason


@dataclass
class Repository:
    name: str
    base_branch: str
    path: Path


@dataclass
class Report:
    command: str
    root: str
    body: dict = field(default_factory=dict)
    failures: list = field(default_factory=list)

    def fail(self, check: str, reason: str, repository: str | None = None,
             leaf: str | None = None) -> None:
        item = {"repository": repository, "check": check, "reason": reason}
        if leaf is not None:
            item["leaf"] = leaf
        self.failures.append(item)

    def emit(self, usage_error: bool = False) -> int:
        document = {"schema_version": SCHEMA_VERSION, "command": self.command,
                    "status": "pass" if not self.failures else "fail", "root": self.root}
        document.update(self.body)
        document["failures"] = self.failures
        print(json.dumps(document, indent=2, sort_keys=False))
        if usage_error:
            return 2
        return 0 if not self.failures else 1


# ── Process helpers ─────────────────────────────────────────────────────────

def clean_environment() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update({"GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"})
    return env


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(command, cwd=str(cwd), env=clean_environment(), text=True,
                              capture_output=True, timeout=GIT_TIMEOUT_SECONDS,
                              stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        return subprocess.CompletedProcess(command, 127, "", f"{command[0]}: not found")
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(command, 124, "", f"{command[0]}: timed out")


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return run(["git", *args], repo)


def resolve_commit(repo: Path, revision: str) -> str | None:
    result = git(repo, "rev-parse", "--verify", "--quiet", f"{revision}^{{commit}}")
    return result.stdout.strip() if result.returncode == 0 else None


def is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    return git(repo, "merge-base", "--is-ancestor", ancestor, descendant).returncode == 0


def valid_branch_name(repo: Path, name: str) -> bool:
    return git(repo, "check-ref-format", "--branch", name).returncode == 0


# ── Input parsing ───────────────────────────────────────────────────────────

def read_text(path: Path, check: str) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as error:
        raise UsageError(check, f"cannot read {path}: {error.strerror}") from error


def section(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == heading:
            body = []
            for following in lines[index + 1:]:
                if following.startswith("## "):
                    break
                body.append(following)
            return body
    return []


def parse_pairs(values: list[str] | None, option: str) -> list[tuple[str, str]]:
    pairs = []
    for value in values or []:
        name, separator, other = value.partition("=")
        if not separator or not other.strip():
            raise UsageError("invalid-repository", f"{option} {value!r} must be NAME=VALUE")
        if not NAME_PATTERN.match(name) or name in {".", ".."}:
            raise UsageError("invalid-repository",
                             f"{option} {value!r}: NAME must be the directory name of a "
                             "repository directly under the root")
        pairs.append((name, other.strip()))
    return pairs


def recorded_repositories(state_text: str | None) -> list[tuple[str, str]] | None:
    if state_text is None:
        return None
    lines = section(state_text, "## Repositories")
    pairs = [match.groups() for match in map(REPOSITORY_LINE.match, lines) if match]
    return pairs or None


def progress_blocks(state_text: str | None) -> list[dict]:
    """Leaf blocks of `## Subtask Progress` with their single-line fields, in file order."""
    blocks: list[dict] = []
    current: dict | None = None
    for line in section(state_text or "", "## Subtask Progress"):
        header = BLOCK_HEADER.match(line)
        if header:
            current = {"id": header.group(2), "composite": bool(header.group(1)), "fields": {}}
            blocks.append(current)
            continue
        field_match = BLOCK_FIELD.match(line)
        if current is not None and field_match:
            current["fields"].setdefault(field_match.group(1), field_match.group(2))
    return [block for block in blocks if not block["composite"]]


def plan_rows(plan_text: str, report: Report) -> list[dict]:
    lines = section(plan_text, "## Subtasks")
    table = [line.strip() for line in lines if line.strip().startswith("|")]
    if len(table) < 2:
        report.fail("plan-invalid", "plan.md has no ## Subtasks table")
        return []

    def cells(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip().strip("|").split("|")]

    header = [cell.lower() for cell in cells(table[0])]
    missing = [name for name in ("id", "depends on", "status") if name not in header]
    if missing:
        report.fail("plan-invalid", f"## Subtasks lacks the column(s): {', '.join(missing)}")
        return []
    column = {name: header.index(name) for name in header}
    rows = []
    for line in table[1:]:
        values = cells(line)
        if all(set(value) <= set("-: ") for value in values):
            continue
        values += [""] * (len(header) - len(values))
        raw_id = values[column["id"]].strip("*` ")
        if not LEAF_ID_PATTERN.match(raw_id):
            report.fail("plan-invalid", f"## Subtasks row has no subtask identifier: {line}")
            continue
        repo = values[column["repo"]].strip("` ") if "repo" in column else ""
        kind = values[column["type"]].strip("` ").lower() if "type" in column else ""
        rows.append({
            "id": raw_id,
            "depends_on": re.findall(LEAF_ID, values[column["depends on"]]),
            "repo": None if repo.lower() in EMPTY_CELLS else repo,
            "composite": kind == "composite",
            "status": values[column["status"]].strip("` ").lower(),
        })
    return rows


# ── Repository set ──────────────────────────────────────────────────────────

def root_in_work_tree(root: Path) -> bool:
    result = git(root, "rev-parse", "--is-inside-work-tree")
    return result.returncode == 0 and result.stdout.strip() == "true"


def candidate_repositories(root: Path) -> list[str]:
    names = []
    for child in sorted(root.iterdir()):
        if child.name.startswith(".") or child.is_symlink() or not child.is_dir():
            continue
        if (child / ".git").exists():
            names.append(child.name)
    return names


def repository_set(root: Path, flags: list[tuple[str, str]], state_text: str | None,
                   report: Report) -> list[Repository] | None:
    names = [name for name, _ in flags]
    if len(set(names)) != len(names):
        raise UsageError("invalid-repository", "a repository is declared more than once")
    recorded = recorded_repositories(state_text)
    if flags and recorded and sorted(flags) != sorted(recorded):
        report.fail("repository-set-mismatch",
                    "the --repo flags differ from the repository set recorded in state.md "
                    f"({', '.join(f'{n}={b}' for n, b in recorded)}); rerun with the recorded "
                    "set or reconcile the task explicitly")
        return None
    chosen = flags or recorded
    if not chosen:
        report.fail("repositories-required",
                    "the root is not a git repository; declare every participating "
                    "repository with --repo <directory>=<base-branch>")
        return None
    return [Repository(name, base, root / name) for name, base in chosen]


def describe(repositories: list[Repository]) -> list[dict]:
    return [{"name": repo.name, "path": str(repo.path), "base_branch": repo.base_branch}
            for repo in repositories]


def repository_root_problem(repo: Repository) -> str | None:
    if repo.path.is_symlink() or not repo.path.is_dir():
        return f"{repo.path} is not a directory"
    result = git(repo.path, "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        return f"{repo.path} is not a git repository"
    if Path(result.stdout.strip()).resolve() != repo.path.resolve():
        return f"{repo.path} is inside {result.stdout.strip()}, not a repository root"
    return None


# ── Commands ────────────────────────────────────────────────────────────────

def command_mode(args, report: Report, root: Path, state_text: str | None) -> None:
    flags = parse_pairs(args.repo, "--repo")
    report.body["candidates"] = candidate_repositories(root)
    if root_in_work_tree(root):
        report.body["mode"] = "single-repository"
        if flags:
            report.fail("root-is-repository",
                        "the root is inside a git work tree; run without --repo to use the "
                        "single-repository rules")
        return
    report.body["mode"] = "multi-repository"
    repositories = repository_set(root, flags, state_text, report)
    if repositories is not None:
        report.body["repositories"] = describe(repositories)


def command_preflight(args, report: Report, root: Path, state_text: str | None) -> None:
    flags = parse_pairs(args.repo, "--repo")
    planned = parse_pairs(args.branch, "--branch")
    report.body["mode"] = "multi-repository"
    report.body["publication"] = "authorized" if args.allow_pr else "not-authorized"
    if root_in_work_tree(root):
        report.body["mode"] = "single-repository"
        report.fail("root-is-repository",
                    "the root is inside a git work tree; use the single-repository preflight")
        return
    repositories = repository_set(root, flags, state_text, report)
    if repositories is None:
        return
    declared = {repo.name for repo in repositories}
    unknown = sorted({name for name, _ in planned} - declared)
    if unknown:
        raise UsageError("invalid-repository",
                         f"--branch names undeclared repositories: {', '.join(unknown)}")
    recorded: dict[str, set[str]] = {}
    for block in progress_blocks(state_text):
        fields = block["fields"]
        if fields.get("repo") and fields.get("branch"):
            recorded.setdefault(fields["repo"], set()).add(fields["branch"])
    report.body["ignored_repositories"] = [name for name in candidate_repositories(root)
                                           if name not in declared]
    results = []
    for repo in repositories:
        branches = [branch for name, branch in planned if name == repo.name]
        results.append(preflight_repository(repo, branches, recorded.get(repo.name, set()),
                                            args.allow_pr, report))
    report.body["repositories"] = results


def preflight_repository(repo: Repository, planned: list[str], recorded: set[str],
                         allow_pr: bool, report: Report) -> dict:
    entry = {"name": repo.name, "path": str(repo.path), "base_branch": repo.base_branch,
             "base_sha": None, "head": None, "tracked_knowledge_paths": None, "checks": []}

    def record(check: str, problem: str | None) -> None:
        entry["checks"].append({"check": check, "status": "fail" if problem else "pass"})
        if problem:
            report.fail(check, problem, repository=repo.name)

    problem = repository_root_problem(repo)
    record("repository", problem)
    if problem:
        return entry
    head = git(repo.path, "symbolic-ref", "--quiet", "--short", "HEAD")
    entry["head"] = head.stdout.strip() if head.returncode == 0 else "detached"

    status = git(repo.path, "status", "--porcelain=v1", "-z", "--untracked-files=no")
    changed = [item[3:] for item in status.stdout.split("\0") if len(item) > 3]
    if status.returncode != 0:
        record("clean-tree", f"git status failed: {status.stderr.strip()}")
    else:
        shown = ", ".join(changed[:20]) + (" …" if len(changed) > 20 else "")
        record("clean-tree", f"uncommitted tracked changes: {shown}" if changed else None)

    git_dir = Path(git(repo.path, "rev-parse", "--absolute-git-dir").stdout.strip())
    active = [marker for marker in OPERATION_MARKERS if (git_dir / marker).exists()]
    record("no-operation-in-progress",
           f"an unfinished git operation is recorded: {', '.join(active)}" if active else None)

    base_sha = None
    if valid_branch_name(repo.path, repo.base_branch):
        base_sha = resolve_commit(repo.path, f"refs/heads/{repo.base_branch}")
    entry["base_sha"] = base_sha
    record("base-branch", None if base_sha else
           f"base branch {repo.base_branch!r} is not a local branch of {repo.name}")

    collisions = []
    for branch in planned:
        if not valid_branch_name(repo.path, branch) or branch == repo.base_branch:
            collisions.append(f"{branch} (invalid name or the base branch)")
        elif resolve_commit(repo.path, f"refs/heads/{branch}") and branch not in recorded:
            collisions.append(f"{branch} (exists and is not recorded for this repository)")
    record("branch-collision", f"planned branch collides: {'; '.join(collisions)}"
           if collisions else None)

    tracked = git(repo.path, "ls-files", "--", ".ai")
    entry["tracked_knowledge_paths"] = len(tracked.stdout.splitlines())

    if allow_pr:
        origin = git(repo.path, "remote", "get-url", "origin")
        record("remote-origin", None if origin.returncode == 0 else
               f"{repo.name} has no remote named origin")
        auth = run(["gh", "auth", "status"], repo.path)
        record("gh-auth", None if auth.returncode == 0 else
               f"gh auth status failed in {repo.name}: "
               f"{(auth.stderr or auth.stdout).strip()[:300]}")
    return entry


def command_route(args, report: Report, root: Path, state_text: str | None) -> None:
    flags = parse_pairs(args.repo, "--repo")
    plan_path = Path(args.plan).resolve()
    rows = plan_rows(read_text(plan_path, "plan-unreadable"), report)
    repositories = repository_set(root, flags, state_text, report)
    if repositories is None or not rows:
        return
    by_name = {repo.name: repo for repo in repositories}
    by_id = {row["id"]: row for row in rows}
    composites = {row["id"]: [child["id"] for child in rows
                              if re.match(rf"^{re.escape(row['id'])}[a-z](?:-fix-|$)",
                                          child["id"])]
                  for row in rows if row["composite"]}
    leaves = [row for row in rows if not row["composite"]]
    parent_of = {child: cid for cid, children in composites.items() for child in children}

    for cid, children in composites.items():
        repos = {by_id[c]["repo"] or by_id[cid]["repo"] for c in children} | {by_id[cid]["repo"]}
        repos.discard(None)
        if len(repos) > 1:
            report.fail("composite-spans-repositories",
                        f"composite {cid} has children in {', '.join(sorted(repos))}; a "
                        "composite and its children belong to one repository", leaf=cid)
        for child in children:
            by_id[child]["repo"] = by_id[child]["repo"] or by_id[cid]["repo"]

    def expand(dependency: str) -> list[str]:
        return composites.get(dependency, [dependency])

    dependencies: dict[str, list[str]] = {}
    gates: dict[str, list[str]] = {}
    for leaf in leaves:
        wanted = list(leaf["depends_on"])
        if leaf["id"] in parent_of:
            wanted += by_id[parent_of[leaf["id"]]]["depends_on"]
        resolved = []
        for dependency in wanted:
            if dependency not in by_id:
                report.fail("unknown-dependency", f"{leaf['id']} depends on unknown "
                            f"{dependency}", leaf=leaf["id"])
                continue
            for item in expand(dependency):
                if item != leaf["id"] and item not in resolved:
                    resolved.append(item)
            if dependency in composites and dependency != parent_of.get(leaf["id"]):
                gates.setdefault(leaf["id"], []).append(dependency)
        dependencies[leaf["id"]] = resolved
        if leaf["repo"] not in by_name:
            report.fail("unrouted-leaf", f"{leaf['id']} has Repo {leaf['repo']!r}; every leaf "
                        "needs exactly one declared repository", leaf=leaf["id"])
    check_working_dirs(plan_path.parent, leaves, by_name, report)

    order = topological_order(leaves, dependencies, report)
    blocks = {block["id"]: block["fields"] for block in progress_blocks(state_text)}
    build_route(order, by_id, dependencies, gates, by_name, blocks, report)


def check_working_dirs(task_dir: Path, leaves: list[dict], repositories: dict,
                       report: Report) -> None:
    known = [leaf["id"] for leaf in leaves]
    directories: dict[str, list[Path]] = {}
    for child in sorted(task_dir.iterdir()) if task_dir.is_dir() else []:
        if not child.is_dir():
            continue
        owners = [leaf for leaf in known if child.name == leaf or child.name.startswith(leaf + "-")]
        if owners:
            directories.setdefault(max(owners, key=len), []).append(child)
    for leaf in leaves:
        repo = repositories.get(leaf["repo"])
        if repo is None:
            continue
        found = directories.get(leaf["id"], [])
        if len(found) != 1:
            report.fail("description-missing" if not found else "description-ambiguous",
                        f"{leaf['id']} needs exactly one subtask directory, found {len(found)}",
                        leaf=leaf["id"])
            continue
        description = found[0] / "description.md"
        match = WORKING_DIR.search(read_text(description, "description-unreadable"))
        if not match or not match.group(1).strip("` "):
            report.fail("working-dir-missing", f"{description} has no working_dir: line",
                        repository=repo.name, leaf=leaf["id"])
            continue
        target = Path(match.group(1).strip("` "))
        resolved = (target if target.is_absolute() else found[0] / target).resolve()
        if resolved != repo.path.resolve():
            report.fail("working-dir-mismatch",
                        f"{leaf['id']} working_dir resolves to {resolved}, but its Repo is "
                        f"{repo.name} ({repo.path})", repository=repo.name, leaf=leaf["id"])


def topological_order(leaves: list[dict], dependencies: dict[str, list[str]],
                      report: Report) -> list[str]:
    """Kahn's algorithm; among ready leaves the earliest plan row runs first."""
    remaining = [leaf["id"] for leaf in leaves]
    done: list[str] = []
    while remaining:
        ready = [leaf for leaf in remaining
                 if all(dep in done or dep not in remaining + done
                        for dep in dependencies.get(leaf, []))]
        if not ready:
            report.fail("dependency-cycle", "Depends On forms a cycle among "
                        f"{', '.join(remaining)}")
            break
        done.append(ready[0])
        remaining.remove(ready[0])
    return done


def build_route(order: list[str], by_id: dict, dependencies: dict, gates: dict,
                repositories: dict, blocks: dict, report: Report) -> None:
    """A leaf is ready when its dependencies, any composite it depends on (reviewed only
    after integration validation) and its same-repository stack parent are reviewed."""
    stacks: dict[str, list[str]] = {name: [] for name in repositories}
    for leaf in order:
        if by_id[leaf]["repo"] in stacks:
            stacks[by_id[leaf]["repo"]].append(leaf)
    reviewed = {leaf for leaf in order if by_id[leaf]["status"] == "reviewed"}
    entries, cross, next_leaf = [], [], None
    for leaf in order:
        repo = by_id[leaf]["repo"]
        if repo not in stacks:
            continue
        stack = stacks[repo]
        position = stack.index(leaf)
        parent = stack[position - 1] if position else None
        base = (blocks.get(parent, {}).get("branch") or None) if parent else \
            repositories[repo].base_branch
        cross_deps = [dep for dep in dependencies[leaf] if by_id[dep]["repo"] != repo]
        cross += [{"leaf": leaf, "repository": repo, "depends_on": dep,
                   "depends_on_repository": by_id[dep]["repo"]} for dep in cross_deps]
        branch = blocks.get(leaf, {}).get("branch") or None
        entries.append({"id": leaf, "repository": repo, "status": by_id[leaf]["status"],
                        "depends_on": dependencies[leaf],
                        "cross_repository_depends_on": cross_deps, "stack_parent": parent,
                        "base_branch": base, "branch": branch,
                        "stack_position": f"{position + 1} of {len(stack)}"})
        if next_leaf is None and leaf not in reviewed:
            waiting = [dep for dep in dependencies[leaf] if dep not in reviewed]
            waiting += [gate for gate in gates.get(leaf, [])
                        if by_id[gate]["status"] != "reviewed"]
            reason = None
            if waiting:
                reason = f"waiting for {', '.join(waiting)} to be reviewed"
            elif parent and parent not in reviewed:
                reason = f"waiting for stack parent {parent} to be reviewed"
            elif parent and base is None:
                reason = f"stack parent {parent} has no recorded branch"
            next_leaf = {"id": leaf, "repository": repo, "stack_parent": parent,
                         "base_branch": base, "branch": branch, "ready": reason is None,
                         "reason": reason}
    report.body.update({"order": entries, "stacks": stacks,
                        "cross_repository_dependencies": cross, "next": next_leaf})


def command_reconcile(args, report: Report, root: Path, state_text: str | None) -> None:
    if state_text is None:
        raise UsageError("state-unreadable", "reconcile needs --state")
    repositories = repository_set(root, parse_pairs(args.repo, "--repo"), state_text, report)
    if repositories is None:
        return
    by_name = {repo.name: repo for repo in repositories}
    invalid = {}
    for repo in repositories:
        problem = repository_root_problem(repo)
        if problem:
            invalid[repo.name] = problem
            report.fail("repository", problem, repository=repo.name)
    blocks = [block for block in progress_blocks(state_text) if block["fields"].get("branch")]
    branches_by_repo: dict[str, set[str]] = {}
    for block in blocks:
        fields = block["fields"]
        branches_by_repo.setdefault(fields.get("repo", ""), set()).add(fields["branch"])
    last_holder = {}
    for block in blocks:
        last_holder[(block["fields"].get("repo"), block["fields"]["branch"])] = block["id"]
    checkpoints = []
    for block in blocks:
        checkpoints.append(reconcile_block(block, by_name, invalid, branches_by_repo,
                                           last_holder, report))
    report.body["checkpoints"] = checkpoints


def reconcile_block(block: dict, repositories: dict, invalid: dict, branches_by_repo: dict,
                    last_holder: dict, report: Report) -> dict:
    fields = block["fields"]
    leaf, branch, repo_name = block["id"], fields["branch"], fields.get("repo")
    entry = {"leaf": leaf, "repository": repo_name, "branch": branch,
             "base_branch": fields.get("base_branch"), "base_commit": fields.get("base_commit"),
             "tip": None, "result": "consistent"}

    def fail(check: str, reason: str) -> dict:
        if entry["result"] == "consistent":
            entry["result"] = check
        report.fail(check, reason, repository=repo_name if check != "repository-unrecorded"
                    else None, leaf=leaf)
        return entry

    if not repo_name:
        return fail("repository-unrecorded", f"{leaf} records branch {branch} without repo:; "
                    "the checkpoint cannot be matched to a repository")
    repo = repositories.get(repo_name)
    if repo is None:
        return fail("repository-unknown", f"{leaf} records repo: {repo_name}, which is not in "
                    "the repository set")
    if repo_name in invalid:
        entry["result"] = "repository"
        return entry
    tip = resolve_commit(repo.path, f"refs/heads/{branch}")
    if tip is None:
        return fail("missing-branch", f"{leaf}: branch {branch} is absent from {repo_name}; "
                    "absence never proves a merge — resolve it explicitly before resuming")
    entry["tip"] = tip
    base_branch = fields.get("base_branch") or ""
    allowed_bases = {repo.base_branch} | (branches_by_repo.get(repo_name, set()) - {branch})
    if base_branch not in allowed_bases:
        fail("base-branch-unrecognized", f"{leaf}: base_branch {base_branch!r} is neither the "
             f"base branch of {repo_name} nor a branch recorded for it")
    base = resolve_commit(repo.path, fields.get("base_commit") or "") \
        if fields.get("base_commit") else None
    if not fields.get("base_commit"):
        return fail("base-commit-missing", f"{leaf}: no base_commit is recorded")
    if base is None:
        return fail("base-commit-unknown", f"{leaf}: base_commit {fields['base_commit']} does "
                    f"not exist in {repo_name}")
    if not is_ancestor(repo.path, base, tip):
        fail("base-not-ancestor", f"{leaf}: base_commit {base} is not an ancestor of "
             f"{branch} ({tip})")
    recorded = []
    for sha in SHA_ENTRY.findall(fields.get("commits") or ""):
        full = resolve_commit(repo.path, sha)
        if full is None:
            fail("commit-unknown", f"{leaf}: recorded commit {sha} does not exist in {repo_name}")
        elif not is_ancestor(repo.path, full, tip):
            fail("commit-not-on-branch", f"{leaf}: recorded commit {sha} is not on {branch}")
        else:
            recorded.append(full)
    if last_holder.get((repo_name, branch)) == leaf:
        expected = recorded[-1] if recorded else base
        if expected != tip:
            fail("unexpected-tip", f"{leaf}: {branch} is at {tip}, but the last recorded "
                 f"checkpoint is {expected}; reconcile the unrecorded commits explicitly")
    return entry


COMMANDS = {"mode": command_mode, "preflight": command_preflight, "route": command_route,
            "reconcile": command_reconcile}


def parser() -> argparse.ArgumentParser:
    main = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = main.add_subparsers(dest="command", required=True)
    for name in COMMANDS:
        command = sub.add_parser(name)
        command.add_argument("--root", required=True)
        command.add_argument("--repo", action="append", metavar="NAME=BASE")
        command.add_argument("--state")
        if name == "preflight":
            command.add_argument("--branch", action="append", metavar="NAME=BRANCH")
            command.add_argument("--allow-pr", action="store_true")
        if name == "route":
            command.add_argument("--plan", required=True)
    return main


def main(argv: list[str]) -> int:
    args = parser().parse_args(argv)
    root = Path(args.root).resolve()
    report = Report(args.command, str(root))
    try:
        if not root.is_dir():
            raise UsageError("invalid-root", f"{args.root} is not a directory")
        state_text = read_text(Path(args.state), "state-unreadable") if args.state else None
        COMMANDS[args.command](args, report, root, state_text)
    except UsageError as error:
        report.fail(error.check, error.reason)
        return report.emit(usage_error=True)
    return report.emit()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
