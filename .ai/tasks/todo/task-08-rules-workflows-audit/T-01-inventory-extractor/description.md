## Goal
`extract` writes a deterministic inventory of the audited files, their text structure and the readers, without changing anything else.

## Context
- Dependencies: none
- Constraints: Python 3.11+ standard library only; type annotations on every function; functions small and single-purpose; `python3 -I` invocation; data-contract names fixed by the specification (JSON keys, diagnostic codes, id prefixes) are used verbatim, while comments, docstrings and test names state rules in words without requirement, criterion or specification labels. Source contract: spec `## Data Model` DM-1, DM-2, DM-3, DM-5 (lines, front matter, fences, headings, sections) and `## Contracts & Interfaces` (CLI, exit codes, Git use).
- Reason: The file and reader inventory with its text model is the base every later part of the tool reads; it has one done-state: a byte-stable inventory without edges.

Off-limits: no change to `rules/`, `workflows/`, `harness/`, `templates/`, `principles/`, `hooks/`, `tests/`, `scripts/validate-contracts.sh`, `scripts/sync.sh`, any other existing script or any specification; no registration of a check in the validator or in sync; never run `scripts/sync.sh`, an installer, a workflow or a model for the inventory; never read or change installed copies; no absolute path and no former repository name in any output; fixtures use synthetic stems, never this repository's names.

## Scope
- **In scope:** the module skeleton with the runtime guard; the `extract` subcommand and its exit codes; audited-set and reader discovery with classes and exclusions; per-file digests, bytes, lines, encoding, words, front matter, invocation lines and sections; git reads for revision, tracked state and work-tree state; `inventory_digest`; atomic write of `--out`; the suite skeleton with fixture-root and git helpers.
- **Out of scope:** edges, candidates, legacy mentions and duplicate clusters (their list keys are emitted empty here); `verify` and `render`.
- **Target files:** `scripts/audit-instructions.py`, `scripts/check-audit-instructions.py`

## Steps
1. Create the suite with helpers that build a fixture root under a temporary directory, optionally initialise git with isolated `HOME` and `XDG_CONFIG_HOME`, and run the tool as a subprocess with `python3 -I`.
2. Write failing cases for the criteria below, then create the tool with its docstring, `from __future__ import annotations`, `import sys` and the version guard as the first statements, and an argument parser for `extract --root --out`.
3. Walk `rules/`, `workflows/`, `harness/` and `templates/codex-global-AGENTS.md` with `os.lstat`, never following links; emit one DM-2 entry per non-directory entry with `set` and `entry`.
4. Compute `sha256`, `bytes`, `lines`, `encoding` (strict UTF-8; U+001C–U+001F is `control-character`) and `words` (`len(text.split())`) for regular files; null for other entries.
5. Implement the text model: LF lines with trailing CR ignored for matching, front matter with `status`, `keys`, `trigger`, `description`, `continuation_lines`, fences with indentation, ATX headings outside fences, and level-2 sections with `(preamble)` whose words and bytes sum to the file's.
6. Count `Invocation: ` lines outside fences for decodable Markdown files.
7. Walk readers with `os.walk(followlinks=False)`, skip `.git/`, `logs/`, `output/`, `__pycache__/`, `*.pyc`, audited files, the three audit-output name patterns and the tool's own two scripts; assign the first matching class; record `decoded: false` for a reader that is not valid UTF-8.
8. Run only the three permitted git read commands with `LC_ALL=C`, `GIT_OPTIONAL_LOCKS=0` and no pager; map failure or absence to null or `unknown`.
9. Build `worktree`, `inventory_digest` and the DM-1 object in key order; write it with `json.dumps(..., ensure_ascii=False, indent=2)` plus one newline to a temporary file in the target directory and move it into place.
10. Return exit 2 for a root without `rules/` or `workflows/`, an unwritable `--out` and a usage error, each with one `ERROR:` line on standard error.

## Acceptance Criteria
- Given a fixture root with `rules/a-b.md`, `rules/reference/c.md`, `workflows/d-e.md` and `harness/x/y.json`, `extract` exits 0 and `files` holds exactly those four paths.
- Two `extract` runs on one fixture root produce byte-identical files, and `inventory_digest` equals the SHA-256 the case computes independently from the path, set-or-class and digest lines.
- With `rules/link.md` linking to a file outside the root and `workflows/sub` linking to a directory, both are rows with `entry: symlink` and null digests, and nothing behind them is read.
- Readers of each class get the DM-3 class, a non-UTF-8 reader has `decoded: false`, and a fixture `docs/audits/2020-01-01-rules-workflows-audit.md` and fixture copies of the tool's two scripts appear in no `readers` entry.
- After `extract` on a fixture root, the SHA-256 of every pre-existing file is unchanged and the only new file is `--out`.
- With `sys.version_info` patched below 3.11 the tool prints `ERROR: Python 3.11 or newer is required` and exits 2; its imports are all in `sys.stdlib_module_names`; `ast.parse` shows the docstring, the future import, `import sys` and the guard `if` as the first statements.
- A fixture file with front matter, a fenced `## ` line, CRLF endings and a preamble yields the front-matter fields and sections the text model defines, with section words and bytes summing to the file's.
- `python3 -I scripts/check-audit-instructions.py` exits 0 and `grep -n 'audit-instructions' scripts/validate-contracts.sh scripts/sync.sh` prints nothing.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - four-path fixture → exactly four `files` rows
  - two runs → identical bytes and independently computed digest
  - symbolic links → `symlink` rows, null digests
  - reader classes, undecodable reader and exclusions → as stated
  - tree digests before and after → only `--out` new
  - patched version → guard message and exit 2; AST and import checks pass
  - text-model fixture → expected front matter and sections
  - suite exits 0; validator and sync do not name the tool
- **Edge cases:** empty file; file without final newline; unclosed front matter; unclosed fence; UTF-8 byte-order mark; invalid UTF-8 and control characters in an audited file; root without git; dirty work tree; missing `rules/` directory; unwritable output path.
