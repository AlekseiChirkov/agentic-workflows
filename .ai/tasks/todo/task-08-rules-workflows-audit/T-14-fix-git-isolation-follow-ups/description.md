## Goal
The tool's git reads match how git itself reads attribute and repository metadata files, the module docstring states the git-version boundary of that isolation, a root below the repository top level reads its work-tree state as unknown instead of clean, and a container matrix runs the suite on the git versions the docstring names.

## Context
- Dependencies: T-13.
- Source: improvement proposals of T-11 (three Do Now items, the Do Later version matrix, two Optional items) and T-01 P3, all ordered applied by the owner on 2026-11-18. Verified by a read-only planning pass:
  - `information_attribute_filters`: the 2048-byte line limit check (scripts/audit-instructions.py:1461-1464) runs on the uncut line, and the `filter=` regex (:187) only excludes NUL from the name. git measures and parses each info/attributes line as a C string. Decision: cut each line at its first NUL before measuring it and before matching. Fixture: `*.md filter=kappa` + NUL + 3000 bytes must leave no marker and keep the tree `clean` (git ≥ 2.41).
  - Module docstring: name the version boundary of git's line and file limits — they arrived with the January 2023 security releases (2.30.7, 2.31.6, 2.32.5, 2.33.6, 2.34.6, 2.35.6, 2.36.4, 2.37.5, 2.38.3, 2.39.1, and every later release). State as a residual that a git from 2.31.0 to 2.39.0 without that release can read a longer line and run a filter it names. Add the phrase to the docstring tests red-first.
  - `read_git_metadata` opens with `os.open` and no prior `os.stat` (:1371); `metadata_text` strips all trailing whitespace (:1387). Decision: `os.stat` the path and reject anything that is not a regular file before `os.open`, keeping the `fstat` check after it (as git does for the `.git` file), so a link to a device node is never opened; strip only trailing CR and LF from the `.git` file and from `commondir`.
  - T-11 Optional 1, decision: keep the current behaviour — an invalid `.git` directory (no `HEAD`, `objects` or `refs`) fails closed and reads `unknown`; returning None would let git find a parent repository without the empty attribute source. State it in the docstring.
  - T-11 Optional 2: add a separate runbook bullet in `.ai/context/runbook.md` (audit paragraph) suggesting `git update-index --refresh` before `extract`, because tree, user and system attributes no longer apply and LFS, ident or eol-converted files with stale stat data can read as changed. The bullet must not contain `audit-instructions.py verify`: the suite's audit-scope note test requires exactly one such bullet.
  - T-01 P3, decision: a root without its own `.git` entry (a directory below the repository top level) gets worktree `{"state": "unknown", "paths": []}` and `git status` is not run. Today it reads `clean` because top-level-relative paths fail the work-tree path filter (:1545-1551). This uses no new git command. Rewrite the docstring sentence "Below the top level … mismatched work-tree paths" and keep the phrase "top level". The delivered inventory was extracted at the top level, so it is unaffected.
  - Version matrix (T-11 Do Later): Docker 29.9.2 is installed and the user is in the `docker` group; no base image is cached; network access was not checked. Build git from kernel.org source tarballs inside a `python:3.12-slim` image (`build-essential zlib1g-dev`; `make NO_CURL=1 NO_EXPAT=1 NO_TCLTK=1 NO_GETTEXT=1 NO_PERL=1 NO_PYTHON=1 prefix=/opt/git install`), because distributions backport the security limits. Versions: 2.30.6, 2.30.7, 2.31.0, 2.31.8, 2.40.1, 2.41.0, 2.44.2, 2.45.0, 2.53.0. Each run mounts the repository read-only with `PYTHONDONTWRITEBYTECODE=1` and runs the suite. Existing tests skip below their minimum version through the suite's version gate; add a few cases gated by a maximum version that confirm the documented residuals (tree filter runs below 2.41, info/attributes filter below 2.31, long line read below the January 2023 releases). Place the matrix files under `scripts/audit-git-matrix/` (Dockerfile and `run.sh`), outside the validator inventory: confirm with the complete validator that it still passes. If the network or the image build is unavailable, deliver the files, run what can run, and record exactly what did not run and why.
- Constraints: as T-13 (standard library only, annotations, verify writes nothing, no new git command, no planning identifiers in product content, frozen tests amended only when wrong with a recorded reason, `METHOD_VERSION` unchanged).
- Off-limits: as T-13, except `.ai/context/runbook.md` (one bullet) and the new `scripts/audit-git-matrix/` directory.

## Scope
- **In scope:** the items above.
- **Out of scope:** verifier form rules, output escaping, render; spec 08 text.
- **Target files:** `scripts/audit-instructions.py`, `scripts/check-audit-instructions.py`, `.ai/context/runbook.md`, `scripts/audit-git-matrix/Dockerfile`, `scripts/audit-git-matrix/run.sh`

## Steps
1. Failing tests: the NUL-cut fixture; `read_git_metadata` on a symbolic link to `/dev/null` never calls `os.open` (in-process test with a patched `os.open`); a `.git` file `gitdir: repo-dir ` + CRLF whose real directory is named `repo-dir ` (trailing space) keeps isolation; a root below the top level of a dirty repository reads `unknown`; the two docstring phrases; the runbook bullet.
2. Implement.
3. Build and run the matrix; record the per-version results.
4. Full suite on the host; delivery gate; complete validator.

## Acceptance Criteria
- Each behaviour in Steps 1 holds and has a test that failed before its implementation.
- No earlier test changes except phrase additions red-first.
- Suite exits 0 on the host; the delivery gate prints `GATE PASS`; `bash scripts/validate-contracts.sh` reports 0 failed.
- The matrix files exist and their recorded runs (or the recorded reason they could not run) are in `notes:`.

## Test Plan
- **Level:** integration (disposable git repositories) plus the container matrix.
- **Scenarios:** as Steps 1; matrix runs per version.
- **Edge cases:** a `.git` file with only LF; a NUL at column 0; `commondir` with a trailing CR.
