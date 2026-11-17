#!/usr/bin/env python3
"""Acceptance suite for multi-repository /spec-run runs.

Two parts:
- behaviour of scripts/repo-set.py against disposable git repositories built under a
  private temporary directory (no real project, branch or remote is touched), and
- the workflow and rule text contract that routes a run through that helper.

Usage: python3 scripts/check-repo-set.py [-v] [unittest arguments]
Exit 0 = every check passed, 1 = at least one failure.
Standalone: it is outside the contract validator's frozen inventory, like
scripts/check-spec-draft.sh. Requires Python 3.9+ and git.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
HELPER = SOURCE_ROOT / "scripts" / "repo-set.py"
REAL_GIT = shutil.which("git")

TASK_REL = Path(".ai/tasks/todo/task-05-user-dashboard")
SPEC_REL = Path(".ai/specs/05-user-dashboard.md")

PLAN = """# plan.md

## Subtasks

| ID | Name | Key Steps (summary) | Depends On | Repo | Status |
|----|------|---------------------|------------|------|--------|
| T-03 | Dashboard screen | route → sections | T-01 | frontend | {T-03} |
| T-01 | Watchlist API | model → endpoint | — | backend | {T-01} |
| T-02 | Openings API | model → endpoint | T-01 | backend | {T-02} |
| T-04 | Opening capture | hook → retry | T-02, T-03 | frontend | {T-04} |

## Execution Strategy
Strictly sequential.
"""

COMPOSITE_PLAN = """## Subtasks

| ID | Name | Key Steps (summary) | Depends On | Type | Repo | Status |
|----|------|---------------------|------------|------|------|--------|
| T-01 | Watchlist API | model → endpoint | — | leaf | backend | not-started |
| T-05 | Activity | (children: T-05a, T-05b) | T-01 | composite | | not-started |
| T-05a | Activity API | a → b | — | leaf | backend | not-started |
| T-05b | Activity view | a → b | — | leaf | frontend | not-started |
"""

DESCRIPTION = """## Goal
{goal}

## Context
- working_dir: {working_dir}
- Dependencies: none
- Constraints: none
- Reason: separate unit

Off-limits: none

## Scope
- **In scope:** x
- **Out of scope:** y
- **Target files:** z

## Steps
1. a

## Acceptance Criteria
- a

## Test Plan
- **Level:** unit
"""

LEAVES = {
    "T-01": ("watchlist-api", "backend", "Expose the personal watchlist API"),
    "T-02": ("openings-api", "backend", "Expose the opening history API"),
    "T-03": ("dashboard-screen", "frontend", "Render the dashboard screen"),
    "T-04": ("opening-capture", "frontend", "Capture report openings"),
}


def git_env(home: Path) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update({
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "Fixture Author",
        "GIT_AUTHOR_EMAIL": "author@example.invalid",
        "GIT_COMMITTER_NAME": "Fixture Author",
        "GIT_COMMITTER_EMAIL": "author@example.invalid",
        "LC_ALL": "C",
    })
    return env


class Fixture:
    """A shared project root that is not a git repository, with nested repositories."""

    def __init__(self, base: Path):
        self.base = base
        self.home = base / "home"
        self.home.mkdir()
        self.env = git_env(self.home)
        self.root = base / "project"
        self.root.mkdir()
        (self.root / SPEC_REL).parent.mkdir(parents=True)
        (self.root / SPEC_REL).write_text("# User dashboard\n\n## Acceptance Criteria\n- AC-01\n")
        self.task = self.root / TASK_REL
        self.task.mkdir(parents=True)

    def git(self, repo: Path, *args: str, check: bool = True) -> str:
        result = subprocess.run([REAL_GIT, *args], cwd=repo, env=self.env, text=True,
                                capture_output=True)
        if check and result.returncode != 0:
            raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
        return result.stdout.strip()

    def repo(self, name: str, branch: str = "dev", remote: bool = True) -> Path:
        path = self.root / name
        path.mkdir()
        self.git(path, "init", "-q", "-b", branch)
        (path / "README.md").write_text(f"{name}\n")
        self.git(path, "add", "README.md")
        self.git(path, "commit", "-q", "-m", "chore: initial")
        if remote:
            self.git(path, "remote", "add", "origin", f"https://example.invalid/{name}.git")
        return path

    def commit(self, repo: Path, filename: str, message: str) -> str:
        (repo / filename).write_text(message + "\n")
        self.git(repo, "add", filename)
        self.git(repo, "commit", "-q", "-m", message)
        return self.git(repo, "rev-parse", "HEAD")

    def head(self, repo: Path) -> str:
        return self.git(repo, "rev-parse", "HEAD")

    def write_plan(self, statuses: dict[str, str] | None = None, text: str | None = None) -> Path:
        statuses = {**{leaf: "not-started" for leaf in LEAVES}, **(statuses or {})}
        plan = self.task / "plan.md"
        body = text if text is not None else PLAN
        for leaf, status in statuses.items():
            body = body.replace("{" + leaf + "}", status)
        plan.write_text(body)
        return plan

    def write_descriptions(self, overrides: dict[str, str] | None = None) -> None:
        overrides = overrides or {}
        for leaf, (slug, repo, goal) in LEAVES.items():
            directory = self.task / f"{leaf}-{slug}"
            directory.mkdir(exist_ok=True)
            working_dir = overrides.get(leaf, f"../../../../../{repo}")
            (directory / "description.md").write_text(
                DESCRIPTION.format(goal=goal, working_dir=working_dir))

    def write_state(self, blocks: str = "", repositories: str | None = None) -> Path:
        if repositories is None:
            repositories = "- repo: backend | base_branch: dev\n- repo: frontend | base_branch: dev\n"
        text = ("spec_path: .ai/specs/05-user-dashboard.md\nflow: full\n\n## Phases\n"
                "- discovery: complete\n- execution: in-progress\n- validation: not-started\n\n")
        if repositories:
            text += "## Repositories\n" + repositories + "\n"
        text += "## Subtask Progress\n\n" + blocks
        state = self.task / "state.md"
        state.write_text(text)
        return state


def block(leaf: str, repo: str, branch: str, base_branch: str, base_commit: str,
          commits: list[tuple[str, str]], status: str = "complete") -> str:
    commit_text = ", ".join(f"{sha} {message}" for sha, message in commits)
    return (f"{leaf} | {LEAVES[leaf][2]} | atomic-tests: green | atomic-execution: {status} | "
            f"atomic-validation: {status}\n"
            "  last_action: fixture\n  target_files: a.py\n  blocker: none\n  notes:\n"
            f"  repo: {repo}\n  branch: {branch}\n  base_branch: {base_branch}\n"
            f"  base_commit: {base_commit}\n  commits: {commit_text}\n  pr: none\n\n")


def run_helper(fixture: Fixture, *args: str, path_prefix: Path | None = None
               ) -> tuple[int, dict]:
    env = dict(fixture.env)
    if path_prefix is not None:
        env["PATH"] = f"{path_prefix}{os.pathsep}{env.get('PATH', '')}"
    result = subprocess.run([sys.executable, "-I", str(HELPER), *args], env=env, text=True,
                            capture_output=True, cwd=fixture.base)
    try:
        document = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise AssertionError(f"helper printed no JSON (exit {result.returncode}): "
                             f"{result.stdout!r} {result.stderr!r}") from error
    return result.returncode, document


def failures(document: dict) -> set[tuple[str | None, str]]:
    return {(item.get("repository"), item["check"]) for item in document.get("failures", [])}


def snapshot(*trees: Path) -> str:
    """Hash every path, mode, size and content below the given trees, .git included."""
    digest = hashlib.sha256()
    for tree in trees:
        for path in sorted(tree.rglob("*")):
            stat = path.lstat()
            digest.update(f"{path}|{stat.st_mode}|{stat.st_size}|{stat.st_mtime_ns}".encode())
            if path.is_file() and not path.is_symlink():
                digest.update(path.read_bytes())
    return digest.hexdigest()


class HelperCase(unittest.TestCase):
    def setUp(self) -> None:
        if REAL_GIT is None:
            self.skipTest("git is not installed")
        self.temp = tempfile.TemporaryDirectory(prefix="repo-set-")
        self.fx = Fixture(Path(self.temp.name))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def two_repos(self) -> tuple[Path, Path]:
        return self.fx.repo("backend"), self.fx.repo("frontend")

    def repo_args(self) -> list[str]:
        return ["--root", str(self.fx.root), "--repo", "backend=dev", "--repo", "frontend=dev"]


class ModeTests(HelperCase):
    def test_single_repository_project_keeps_the_single_repository_route(self) -> None:
        root = self.fx.base / "single"
        root.mkdir()
        self.fx.git(root, "init", "-q", "-b", "main")
        code, doc = run_helper(self.fx, "mode", "--root", str(root))
        self.assertEqual((code, doc["status"], doc["mode"]), (0, "pass", "single-repository"))

    def test_repository_flags_are_refused_when_the_root_is_a_repository(self) -> None:
        root = self.fx.base / "single"
        root.mkdir()
        self.fx.git(root, "init", "-q", "-b", "main")
        code, doc = run_helper(self.fx, "mode", "--root", str(root), "--repo", "api=main")
        self.assertEqual(code, 1)
        self.assertIn((None, "root-is-repository"), failures(doc))

    def test_shared_root_without_declared_repositories_stops_and_lists_candidates(self) -> None:
        self.two_repos()
        code, doc = run_helper(self.fx, "mode", "--root", str(self.fx.root))
        self.assertEqual(code, 1)
        self.assertIn((None, "repositories-required"), failures(doc))
        self.assertEqual(doc["candidates"], ["backend", "frontend"])

    def test_shared_root_with_declared_repositories_is_multi_repository(self) -> None:
        self.two_repos()
        code, doc = run_helper(self.fx, "mode", *self.repo_args())
        self.assertEqual((code, doc["mode"]), (0, "multi-repository"))
        self.assertEqual([r["name"] for r in doc["repositories"]], ["backend", "frontend"])


class PreflightTests(HelperCase):
    def test_two_clean_repositories_pass_and_undeclared_repositories_are_excluded(self) -> None:
        backend, frontend = self.two_repos()
        self.fx.repo("tools")
        (frontend / "notes.txt").write_text("untracked files are permitted\n")
        code, doc = run_helper(self.fx, "preflight", *self.repo_args())
        self.assertEqual((code, doc["status"]), (0, "pass"), doc)
        names = [repo["name"] for repo in doc["repositories"]]
        self.assertEqual(names, ["backend", "frontend"])
        self.assertEqual(doc["ignored_repositories"], ["tools"])
        by_name = {repo["name"]: repo for repo in doc["repositories"]}
        self.assertEqual(by_name["backend"]["base_sha"], self.fx.head(backend))
        self.assertEqual(by_name["frontend"]["base_branch"], "dev")

    def test_dirty_tracked_file_in_one_repository_stops_naming_repository_and_path(self) -> None:
        backend, frontend = self.two_repos()
        (frontend / "README.md").write_text("changed\n")
        code, doc = run_helper(self.fx, "preflight", *self.repo_args())
        self.assertEqual((code, doc["status"]), (1, "fail"))
        self.assertEqual(failures(doc), {("frontend", "clean-tree")})
        reason = next(item["reason"] for item in doc["failures"])
        self.assertIn("README.md", reason)

    def test_missing_base_branch_stops(self) -> None:
        self.fx.repo("backend")
        self.fx.repo("frontend", branch="main")
        code, doc = run_helper(self.fx, "preflight", *self.repo_args())
        self.assertEqual(code, 1)
        self.assertEqual(failures(doc), {("frontend", "base-branch")})

    def test_unfinished_git_operation_stops(self) -> None:
        backend, _ = self.two_repos()
        git_dir = Path(self.fx.git(backend, "rev-parse", "--absolute-git-dir"))
        (git_dir / "MERGE_HEAD").write_text(self.fx.head(backend) + "\n")
        code, doc = run_helper(self.fx, "preflight", *self.repo_args())
        self.assertEqual(code, 1)
        self.assertIn(("backend", "no-operation-in-progress"), failures(doc))

    def test_declared_path_that_is_not_a_repository_root_stops(self) -> None:
        self.fx.repo("backend")
        (self.fx.root / "frontend").mkdir()
        code, doc = run_helper(self.fx, "preflight", *self.repo_args())
        self.assertEqual(code, 1)
        self.assertIn(("frontend", "repository"), failures(doc))

    def test_nested_or_escaping_repository_names_are_refused(self) -> None:
        self.two_repos()
        for name in ("../backend", "backend/src", "."):
            with self.subTest(name=name):
                code, doc = run_helper(self.fx, "preflight", "--root", str(self.fx.root),
                                       "--repo", f"{name}=dev")
                self.assertEqual(code, 2)
                self.assertIn("invalid-repository", {item["check"] for item in doc["failures"]})

    def test_planned_branch_collision_stops_unless_recorded_for_that_repository(self) -> None:
        backend, _ = self.two_repos()
        self.fx.git(backend, "branch", "feat/watchlist-api")
        code, doc = run_helper(self.fx, "preflight", *self.repo_args(),
                               "--branch", "backend=feat/watchlist-api")
        self.assertEqual(code, 1)
        self.assertEqual(failures(doc), {("backend", "branch-collision")})
        base = self.fx.head(backend)
        state = self.fx.write_state(block("T-01", "backend", "feat/watchlist-api", "dev", base, []))
        code, doc = run_helper(self.fx, "preflight", *self.repo_args(), "--state", str(state),
                               "--branch", "backend=feat/watchlist-api")
        self.assertEqual((code, doc["status"]), (0, "pass"), doc)

    def test_recorded_repository_set_is_reused_and_a_different_one_stops(self) -> None:
        self.two_repos()
        state = self.fx.write_state()
        code, doc = run_helper(self.fx, "preflight", "--root", str(self.fx.root),
                               "--state", str(state))
        self.assertEqual((code, [r["name"] for r in doc["repositories"]]),
                         (0, ["backend", "frontend"]))
        code, doc = run_helper(self.fx, "preflight", "--root", str(self.fx.root),
                               "--state", str(state), "--repo", "backend=main",
                               "--repo", "frontend=dev")
        self.assertEqual(code, 1)
        self.assertIn((None, "repository-set-mismatch"), failures(doc))


class PublicationTests(HelperCase):
    def recorder(self) -> tuple[Path, Path]:
        """Fake gh and a git wrapper that log every invocation, then defer to real git."""
        bin_dir = self.fx.base / "bin"
        bin_dir.mkdir()
        log = self.fx.base / "calls.log"
        (bin_dir / "gh").write_text(f"#!/bin/sh\necho \"gh $*\" >> '{log}'\nexit 0\n")
        (bin_dir / "git").write_text(f"#!/bin/sh\necho \"git $*\" >> '{log}'\n"
                                     f"exec '{REAL_GIT}' \"$@\"\n")
        for name in ("gh", "git"):
            (bin_dir / name).chmod(0o755)
        log.write_text("")
        return bin_dir, log

    def test_without_allow_pr_no_gh_and_no_network_git_command_runs(self) -> None:
        self.two_repos()
        bin_dir, log = self.recorder()
        code, doc = run_helper(self.fx, "preflight", *self.repo_args(), path_prefix=bin_dir)
        self.assertEqual(code, 0, doc)
        calls = log.read_text().splitlines()
        self.assertTrue(any(call.startswith("git ") for call in calls))
        self.assertFalse([call for call in calls if call.startswith("gh ")])
        self.assertFalse([call for call in calls
                          if re.search(r"\b(push|fetch|pull|ls-remote|clone)\b", call)])
        self.assertEqual(doc["publication"], "not-authorized")

    def test_allow_pr_checks_origin_and_authentication_in_every_repository(self) -> None:
        self.fx.repo("backend")
        self.fx.repo("frontend", remote=False)
        bin_dir, log = self.recorder()
        code, doc = run_helper(self.fx, "preflight", *self.repo_args(), "--allow-pr",
                               path_prefix=bin_dir)
        self.assertEqual(code, 1)
        self.assertEqual(failures(doc), {("frontend", "remote-origin")})
        gh_calls = [call for call in log.read_text().splitlines() if call.startswith("gh ")]
        self.assertTrue(gh_calls)
        self.assertTrue(all(call.startswith("gh auth status") for call in gh_calls))
        self.assertFalse(re.search(r"\b(push|fetch|pull)\b", log.read_text()))


class RouteTests(HelperCase):
    def prepared(self, statuses: dict[str, str] | None = None, blocks: str = "") -> list[str]:
        self.two_repos()
        plan = self.fx.write_plan(statuses)
        self.fx.write_descriptions()
        state = self.fx.write_state(blocks)
        return ["route", "--root", str(self.fx.root), "--plan", str(plan), "--state", str(state)]

    def test_independent_stacks_follow_one_shared_topological_order(self) -> None:
        code, doc = run_helper(self.fx, *self.prepared())
        self.assertEqual((code, doc["status"]), (0, "pass"), doc)
        self.assertEqual([leaf["id"] for leaf in doc["order"]], ["T-01", "T-03", "T-02", "T-04"])
        self.assertEqual(doc["stacks"], {"backend": ["T-01", "T-02"], "frontend": ["T-03", "T-04"]})
        by_id = {leaf["id"]: leaf for leaf in doc["order"]}
        self.assertEqual((by_id["T-01"]["stack_parent"], by_id["T-01"]["base_branch"]),
                         (None, "dev"))
        self.assertEqual((by_id["T-03"]["stack_parent"], by_id["T-03"]["base_branch"]),
                         (None, "dev"))
        self.assertEqual(by_id["T-02"]["stack_parent"], "T-01")
        self.assertEqual(by_id["T-04"]["stack_parent"], "T-03")
        self.assertEqual(by_id["T-04"]["stack_position"], "2 of 2")

    def test_cross_repository_dependencies_are_explicit_and_gate_the_next_leaf(self) -> None:
        code, doc = run_helper(self.fx, *self.prepared())
        self.assertEqual(doc["cross_repository_dependencies"], [
            {"leaf": "T-03", "repository": "frontend", "depends_on": "T-01",
             "depends_on_repository": "backend"},
            {"leaf": "T-04", "repository": "frontend", "depends_on": "T-02",
             "depends_on_repository": "backend"},
        ])
        self.assertEqual((doc["next"]["id"], doc["next"]["ready"]), ("T-01", True))

    def test_dependency_not_reviewed_keeps_the_dependent_leaf_waiting(self) -> None:
        code, doc = run_helper(self.fx, *self.prepared({"T-01": "done"}))
        self.assertEqual(doc["next"]["id"], "T-01")
        statuses = {"T-01": "reviewed", "T-03": "reviewed", "T-02": "blocked"}
        temp_args = self.fx.write_plan(statuses)
        code, doc = run_helper(self.fx, "route", "--root", str(self.fx.root), "--plan",
                               str(temp_args), "--state", str(self.fx.task / "state.md"))
        self.assertEqual(doc["next"]["id"], "T-02")
        self.assertEqual(code, 0)

    def test_resume_selects_the_earliest_unfinished_leaf_on_its_own_stack(self) -> None:
        args = self.prepared({"T-01": "reviewed", "T-03": "reviewed", "T-02": "in-progress"})
        backend, frontend = self.fx.root / "backend", self.fx.root / "frontend"
        b_base = self.fx.head(backend)
        self.fx.git(backend, "checkout", "-q", "-b", "feat/watchlist-api")
        b_tip = self.fx.commit(backend, "w.py", "feat: add watchlist")
        f_base = self.fx.head(frontend)
        self.fx.git(frontend, "checkout", "-q", "-b", "feat/dashboard-screen")
        f_tip = self.fx.commit(frontend, "d.ts", "feat: add dashboard")
        blocks = (block("T-01", "backend", "feat/watchlist-api", "dev", b_base,
                        [(b_tip, "feat: add watchlist")])
                  + block("T-03", "frontend", "feat/dashboard-screen", "dev", f_base,
                          [(f_tip, "feat: add dashboard")]))
        self.fx.write_state(blocks)
        code, doc = run_helper(self.fx, *args)
        self.assertEqual(code, 0, doc)
        self.assertEqual(doc["next"], {"id": "T-02", "repository": "backend",
                                       "stack_parent": "T-01",
                                       "base_branch": "feat/watchlist-api",
                                       "branch": None, "ready": True, "reason": None})
        by_id = {leaf["id"]: leaf for leaf in doc["order"]}
        self.assertEqual(by_id["T-04"]["base_branch"], "feat/dashboard-screen")

    def test_leaf_without_a_declared_repository_is_unroutable(self) -> None:
        self.two_repos()
        text = PLAN.replace("| T-02 | Openings API | model → endpoint | T-01 | backend |",
                            "| T-02 | Openings API | model → endpoint | T-01 | (umbrella) |")
        plan = self.fx.write_plan(text=text)
        self.fx.write_descriptions()
        state = self.fx.write_state()
        code, doc = run_helper(self.fx, "route", "--root", str(self.fx.root), "--plan",
                               str(plan), "--state", str(state))
        self.assertEqual(code, 1)
        self.assertIn(("T-02", "unrouted-leaf"), {(f.get("leaf"), f["check"])
                                                   for f in doc["failures"]})

    def test_working_dir_must_name_the_routed_repository(self) -> None:
        self.two_repos()
        plan = self.fx.write_plan()
        self.fx.write_descriptions({"T-03": "../../../../../backend"})
        state = self.fx.write_state()
        code, doc = run_helper(self.fx, "route", "--root", str(self.fx.root), "--plan",
                               str(plan), "--state", str(state))
        self.assertEqual(code, 1)
        self.assertIn(("T-03", "working-dir-mismatch"), {(f.get("leaf"), f["check"])
                                                          for f in doc["failures"]})

    def test_composite_children_must_share_one_repository(self) -> None:
        self.two_repos()
        plan = self.fx.write_plan(text=COMPOSITE_PLAN)
        for leaf, repo in (("T-01", "backend"), ("T-05a", "backend"), ("T-05b", "frontend")):
            directory = self.fx.task / f"{leaf}-part"
            directory.mkdir()
            (directory / "description.md").write_text(
                DESCRIPTION.format(goal="part", working_dir=f"../../../../../{repo}"))
        state = self.fx.write_state()
        code, doc = run_helper(self.fx, "route", "--root", str(self.fx.root), "--plan",
                               str(plan), "--state", str(state))
        self.assertEqual(code, 1, doc)
        self.assertIn("composite-spans-repositories", {f["check"] for f in doc["failures"]})


class ReconcileTests(HelperCase):
    def recorded(self) -> tuple[Path, Path, str, str, str]:
        backend, frontend = self.two_repos()
        base = self.fx.head(backend)
        self.fx.git(backend, "checkout", "-q", "-b", "feat/watchlist-api")
        red = self.fx.commit(backend, "test_w.py", "test: cover watchlist")
        green = self.fx.commit(backend, "w.py", "feat: add watchlist")
        self.fx.git(backend, "checkout", "-q", "dev")
        state = self.fx.write_state(block("T-01", "backend", "feat/watchlist-api", "dev", base,
                                          [(red[:12], "test: cover watchlist"),
                                           (green[:12], "feat: add watchlist")]))
        return backend, state, base, red, green

    def reconcile(self, state: Path) -> tuple[int, dict]:
        return run_helper(self.fx, "reconcile", "--root", str(self.fx.root), "--state", str(state))

    def test_recorded_checkpoints_that_match_their_repository_are_consistent(self) -> None:
        _, state, *_ = self.recorded()
        code, doc = self.reconcile(state)
        self.assertEqual((code, doc["status"]), (0, "pass"), doc)
        self.assertEqual(doc["checkpoints"][0]["result"], "consistent")

    def test_missing_branch_needs_explicit_resolution_and_is_never_read_as_merged(self) -> None:
        backend, state, *_ = self.recorded()
        self.fx.git(backend, "branch", "-D", "feat/watchlist-api")
        code, doc = self.reconcile(state)
        self.assertEqual(code, 1)
        self.assertEqual(failures(doc), {("backend", "missing-branch")})
        self.assertNotIn("merged", json.dumps(doc["checkpoints"]).replace("never merged", ""))

    def test_unexpected_tip_stops(self) -> None:
        backend, state, *_ = self.recorded()
        self.fx.git(backend, "checkout", "-q", "feat/watchlist-api")
        self.fx.commit(backend, "extra.py", "feat: unrecorded change")
        code, doc = self.reconcile(state)
        self.assertEqual(code, 1)
        self.assertEqual(failures(doc), {("backend", "unexpected-tip")})

    def test_base_commit_that_is_not_an_ancestor_stops(self) -> None:
        backend, state, base, red, green = self.recorded()
        self.fx.git(backend, "checkout", "-q", "dev")
        other = self.fx.commit(backend, "other.py", "chore: unrelated")
        state.write_text(state.read_text().replace(f"base_commit: {base}", f"base_commit: {other}"))
        code, doc = self.reconcile(state)
        self.assertEqual(code, 1)
        self.assertIn(("backend", "base-not-ancestor"), failures(doc))

    def test_checkpoint_without_a_recorded_repository_is_ambiguous(self) -> None:
        _, state, *_ = self.recorded()
        state.write_text(state.read_text().replace("  repo: backend\n", ""))
        code, doc = self.reconcile(state)
        self.assertEqual(code, 1)
        self.assertIn((None, "repository-unrecorded"), failures(doc))

    def test_branch_recorded_in_the_other_repository_is_not_found_there(self) -> None:
        _, state, *_ = self.recorded()
        state.write_text(state.read_text().replace("  repo: backend\n", "  repo: frontend\n"))
        code, doc = self.reconcile(state)
        self.assertEqual(code, 1)
        self.assertIn(("frontend", "missing-branch"), failures(doc))


class ReadOnlyTests(HelperCase):
    def test_every_command_leaves_repositories_and_project_files_unchanged(self) -> None:
        backend, frontend = self.two_repos()
        (frontend / "README.md").write_text("dirty\n")
        plan = self.fx.write_plan()
        self.fx.write_descriptions()
        state = self.fx.write_state()
        before = snapshot(self.fx.root)
        for args in (["mode", *self.repo_args()],
                     ["preflight", *self.repo_args(), "--branch", "backend=feat/x"],
                     ["route", "--root", str(self.fx.root), "--plan", str(plan),
                      "--state", str(state)],
                     ["reconcile", "--root", str(self.fx.root), "--state", str(state)]):
            run_helper(self.fx, *args)
        self.assertEqual(snapshot(self.fx.root), before)


class RealisticLayoutTests(HelperCase):
    def test_shared_specification_outside_both_repositories_reaches_discovery(self) -> None:
        """The InvestAI shape: root .ai/ outside git, backend/ and frontend/ on dev."""
        self.two_repos()
        self.assertNotEqual(subprocess.run([REAL_GIT, "rev-parse", "--git-dir"],
                                           cwd=self.fx.root, env=self.fx.env,
                                           capture_output=True).returncode, 0)
        self.assertTrue((self.fx.root / SPEC_REL).is_file())
        code, doc = run_helper(self.fx, "mode", *self.repo_args())
        self.assertEqual((code, doc["mode"]), (0, "multi-repository"))
        code, doc = run_helper(self.fx, "preflight", *self.repo_args())
        self.assertEqual((code, doc["status"]), (0, "pass"), doc)


def section(text: str, heading: str) -> str:
    match = re.search(rf"^{re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


class InstructionContractTests(unittest.TestCase):
    def contains(self, needle: str, haystack: str) -> None:
        self.assertTrue(needle in haystack, f"missing: {needle}")

    def lacks(self, needle: str, haystack: str) -> None:
        self.assertFalse(needle in haystack, f"still present: {needle}")

    @staticmethod
    def read(relative: str) -> str:
        return (SOURCE_ROOT / relative).read_text(encoding="utf-8")

    def test_spec_run_accepts_a_repository_set_and_keeps_single_repository_rules(self) -> None:
        text = self.read("workflows/spec-run.md")
        self.contains("Invocation: `/spec-run <path-to-spec> [--repo <directory>=<base-branch> ...] "
                      "[--allow-pr] [--dry-run]`", text)
        self.lacks("One repository per invocation", text)
        for command in ("repo-set.py mode", "repo-set.py preflight", "repo-set.py route",
                        "repo-set.py reconcile"):
            self.contains(command, text)
        self.contains("`git-flow → ## Multi-repository runs`", text)
        flat = " ".join(text.split())
        for kept in ("subtask N branches from the tip of subtask N-1",
                     "Never start N+1 before N is `reviewed`",
                     "never infer that missing means merged",
                     "Never runs subtasks in parallel.",
                     "without it run no push or `gh` command"):
            self.contains(kept, flat)

    def test_spec_run_dry_run_stays_read_only_in_both_modes(self) -> None:
        flat = " ".join(self.read("workflows/spec-run.md").split())
        self.contains("In multi-repository mode `--dry-run` runs only the read-only helper "
                      "commands", flat)

    def test_git_flow_defines_multi_repository_runs(self) -> None:
        text = self.read("rules/git-flow.md")
        self.lacks("Single-repo only.", text)
        body = " ".join(section(text, "## Multi-repository runs").split())
        self.assertTrue(body, "git-flow.md has no ## Multi-repository runs section")
        for phrase in ("Run the preflight separately for every participating repository",
                       "never names a branch of another repository as its base",
                       "no shared git history",
                       "Without `--allow-pr`, neither `git push` nor any `gh` command runs",
                       "cross-repository dependencies"):
            self.contains(phrase, body)
        self.assertTrue(re.search(r"(?m)^repo: +backend$", text), "missing: repo: backend")

    def test_state_formats_define_the_repository_set_and_repo_field(self) -> None:
        text = self.read("rules/workflow-globals.md")
        self.assertTrue(re.search(r"(?m)^  repo: <participating repository directory name — "
                                  r"multi-repository orchestrated mode only>$", text),
                        "missing: canonical repo: line")
        self.assertEqual(len(re.findall(r"(?m)^Repository set line: ", text)), 1)
        protected = section(self.read("rules/workflow-reference.md"),
                            "## Protected Sections Contract")
        self.contains("`## Repositories`", protected)
        self.contains("`repo:`", protected)

    def test_discovery_routes_each_leaf_to_one_repository(self) -> None:
        self.contains("## Repositories", self.read("workflows/phase-discovery.md"))
        flat = " ".join(self.read("workflows/pd-decompose.md").split())
        self.contains("When task `state.md` carries `## Repositories`", flat)
        self.contains("one leaf per repository", flat)
        self.contains("Cross-repository dependencies:", flat)

    def test_fixes_and_restack_stay_inside_one_repository(self) -> None:
        self.contains("never group fixes from different repositories",
                      " ".join(self.read("workflows/pv-classify-fixes.md").split()))
        self.contains("extend the stack of their own repository",
                      " ".join(self.read("workflows/pv-create-fixes.md").split()))
        self.contains("--repo <directory>", self.read("workflows/restack.md"))

    def test_quickstart_no_longer_limits_a_spec_to_one_repository(self) -> None:
        text = self.read("docs/SPEC-RUN-QUICKSTART.md")
        self.lacks("One spec covers **one repository**", text)
        self.contains("--repo", text)


if __name__ == "__main__":
    unittest.main()
