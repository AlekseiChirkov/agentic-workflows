flow: quick
kind: bugfix

## Phases
- discovery: complete
- execution: complete
- validation: complete

## Subtask Progress

T-01 | Fix: inline code links in archive relocation (quick, inline; no subtask directory) | atomic-tests: green | atomic-execution: complete | atomic-validation: complete
  branch: fix/finalization-inline-code-links
  base_branch: main
  base_commit: 436f1ef958ca7365f06891a457f24fdcc1bb158d
  commits: dca91f67670da7f2282332543e5dc217ef970347 test(finalization): require links inside inline code to stay text during archive, 426cbb973f9873a4090ade4d86b8b6a0abd4544b test(finalization): require links with inline code in their text to stay relocated and checked, 003227af7df1ea30e32272cef53cd2820e17e64a test(finalization): require a real link after a stray bracket and code to stay relocated and checked, f9ff0748cc0342ebcc89699e997ea0f72515f602 fix(finalization): treat inline code as text when relocating archive links
  pr: #128
  last_action: merged into main as PR #128 after three independent review rounds
  target_files: scripts/finalization_archive.py, scripts/check-finalization-workflow.py
  blocker: none
  notes: quick flow keeps its inline contract and the `## TDD (quick)` record below; this block records the delivery fields

## Defect
source: owner request 2026-11-19 during `/phase-finalize` of task 08 (independent finalization reviewer finding)
description: the archive step's Markdown link relocation skips fenced code blocks but not inline code spans, so an inline code example such as `[/home/x](/home/x/y)` in a task record is parsed as a link and archival refuses with `unsafe-path` before any move.
expected: text inside inline code spans is never treated as a Markdown link, exactly as text inside fenced blocks is not (source: `relocated_document` docstring "prose, fences and historical sections stay exact"; Markdown inline code is literal text).

## Reproduction
trigger: `relocated_document(<task state.md>, …, 'An example: `[/home/x](/home/x/y)` stays text.\n', …)`
observed: `Refusal: Path escapes project: /home/x/y`
expected: the line is returned unchanged
verified_by: `MISE_PYTHON_VERSION=3.12.16 python3 -B <scratch>/repro-inline.py` (calls `scripts/finalization_archive.py:relocated_document` in a temporary root), 2026-11-19
real case: task 08 `state.md` lines 554, 571, 1183 and `T-14-fix-git-isolation-follow-ups/description.md` hold such inline examples; `moving_link_plans` refuses on them

## Diagnosis
cause: `scripts/finalization_archive.py:264-296` — the per-line loop tracks fences and historical sections only; the link pattern is applied to the whole remaining line, inline code spans included, and `safe_path` (`:296`) refuses a target outside the root.
callers: `moving_link_plans` and `pointer_plans` during `archive`; persisted data: none (the refusal happens before writes; `snapshot/current-links` copies may exist).

## Contract (quick)

### Gate
1. files (incl. tests): 2 (`scripts/finalization_archive.py`, `scripts/check-finalization-workflow.py`) → pass
2. new invariant: no → pass
3. behaviour change to a shipped pipeline: yes — the shipped `/phase-finalize` archive step changes which inputs it rewrites or refuses (inline-code examples no longer refuse) → fail
4. schema change / migration: no → pass
verdict: full
owner exception (2026-11-19): the owner accepted the recommendation to fix this defect on the quick path despite condition 3 (the owner accepted the recommendation in chat on 2026-11-19), with a failing test first, the finalization suites, the complete validator and an independent review; rationale: the change narrows a refusal to the behaviour the function's contract already states (prose and code stay exact), two files, no new invariant

### Off-limits
- Task records and historical sections stay byte-exact; no other relocation rule changes.
### Invariants
- Fenced blocks and historical sections stay exact; links outside inline code are relocated and checked as before.
### Acceptance Criteria
- [x] Given a task record line holding a link inside an inline code span, when the archive relocates links, then the line stays byte-identical and no refusal occurs.
- [x] Given a real link to the task outside code, when the archive relocates links, then it is rewritten to the archived path as before.

## Handover
The gate verdict was `full` (condition 3); the owner granted the exception above, so the fix continued on the quick path.

## TDD (quick)
level: integration (temporary finalization fixture roots)
tests: scripts/check-finalization-workflow.py → WorkflowBehavior.test_link_inside_inline_code_is_text_and_never_relocated_or_refused
red-observed: yes — 2026-11-19, `archive` blocked with `unsafe-path: Path escapes project: /home/x/y` (commit dca91f6); the neighbouring scope-index relocation test passed
green-observed: yes — 2026-11-19, the new test passes; scripts/check-finalization-workflow.py 64 OK, scripts/check-phase-finalize.py 77 OK; the reproduction prints `OK unchanged`
target_files: scripts/finalization_archive.py, scripts/check-finalization-workflow.py
implementation (first attempt): split each line at inline code spans and relocated links only in text parts
review round 1 (independent, 2026-11-19): NEEDS WORK — critical: splitting cut links whose text holds inline code (`[`s.md`](path)`), so they were neither relocated nor checked, which would break such links silently when a spec is archived (reproduced on `.ai/specs/21-open-source-readiness.md:172`); optional: an escaped backtick opened a span; patterns compiled per loop; the test covered only the in-code half
rework red: WorkflowBehavior.test_link_whose_text_holds_inline_code_is_still_relocated_and_checked — 4 failing subtests (code in link text, code in a reference label, escaped backticks, an unsafe destination with code text not refused) (commit 426cbb9)
implementation: `code_masked` masks inline code spans (backslash-escaped backticks outside a span open nothing); `relocate_outside_code` finds links on the masked line and relocates them on the original line, so a link whose destination lies inside code stays text while a link whose text holds code is still relocated and checked; patterns compiled once
rework green: scripts/check-finalization-workflow.py 65 OK, scripts/check-phase-finalize.py 77 OK; reviewer probes give the expected results; spec 21's line 172 relocates again
review round 2 (independent, 2026-11-19): NEEDS WORK — important: a stray `[` before a code span holding `]` made the masked search swallow a later real link, so it was neither relocated nor checked (98 of 120,000 fuzzed lines versus a CommonMark parser); optional: a lone backtick in a link title pairs with later code (O1), `[`a]b`](d.md)` not relocated (O2, also in the base code), import grouping (O3)
rework 2 red: two subtests (stray bracket then code then a real link; the same with an unsafe destination) (commit 003227a)
rework 2 green: a failed original match resumes the masked search at the next position; scripts/check-finalization-workflow.py 65 OK, scripts/check-phase-finalize.py 77 OK; O3 fixed; O1 and O2 recorded, not applied (owner rule: minor findings recorded)
whole-repository comparison (round 2 reviewer): relocating every Markdown file differs from the base code only on the 9 lines whose link lies inside inline code, where the base code refused
review round 3 (independent, 2026-11-19): DONE — the stray-bracket case fixed (its subtests fail on a rebuilt round-1 implementation and pass now); link fuzz against micromark over 3×120,000 lines leaves 5–10 base-correct/fix-wrong lines per corpus, all O1 (a backtick inside a link destination or title); whole-repository comparison differs from the base code only on the 9 lines whose link lies inside inline code; loops terminate; suites 65 and 77 OK; complete validator 725 passed, 0 failed, 2 skipped
recorded, not applied: O1, O2

## Validation Result
validation: complete (2026-11-19) — contract: both acceptance criteria met (inline-code links stay byte-identical; real links outside code are relocated and refused as before); ADR trigger: none (bug fix restoring the documented contract)

## Spec Sync
sync: n-a — no specification governs this defect; the fix restores the behaviour that the function's own contract already states (fenced blocks and prose stay exact), so no specification text changes
