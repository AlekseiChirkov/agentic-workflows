## Goal
The archive step of task finalization treats inline code spans as text when it relocates Markdown links, as it already does for fenced blocks, so an example link inside backticks in a task record never refuses archival.

## Context
- Source: owner request 2026-11-19 during the finalization of the rules and workflows audit; an independent finalization reviewer found that archive refused with `unsafe-path` on an inline code example such as `[/home/x](/home/x/y)`.
- Cause: `scripts/finalization_archive.py` `relocated_document` applied the link patterns to whole lines, inline code included.
- Flow: quick, by owner-approved exception to the shipped-pipeline condition of the quick gate (recorded in `state.md`).

## Acceptance Criteria
- A task record line holding a link inside an inline code span stays byte-identical during archival and does not refuse.
- Real links outside code are relocated and refused as before, including links whose text holds code and links after a stray bracket.
