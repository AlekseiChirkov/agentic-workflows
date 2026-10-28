# Open-source readiness: installer, profiles, examples, scrubbing, contributing

## Current implementation baseline — 2026-10-28

The checkout already contains a public README, version stamp, portable source roots,
tracked knowledge and completed hygiene checks. Hook installation has owned-entry
preservation/recovery (`scripts/install-hooks.sh`, `scripts/install-hooks.py`), but it
is not a general workflow installer/uninstaller. Profiles, contribution/release
materials, model goldens, generated references and the wider harness/naming migration
remain pending. The workflow-only audit does not authorize a release or deployment.

## Goal

After spec 01 the repository is public but still shaped for one machine: `sync.sh`
overwrites the user's global files without asking, the Python/FastAPI/GCP standards are
the default for everyone, public hygiene requires re-verification, and there
is no example of a finished task or a contribution guide. Make Orchestrail installable
by a stranger in fifteen minutes and technology-neutral at its core (ADR-0009,
Decisions 1 and 6).

## Acceptance Criteria

- [ ] `install.sh` replaces `sync.sh` for external users: `--dry-run` lists every path it
      would write; a backup of an existing `~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md`
      is taken before overwrite; `--uninstall` removes only unchanged installer-owned paths in the skill
      manifest and restores backups without overwriting later user modifications; `sync.sh` remains the maintainer's deploy
      command and calls the same code
- [ ] `profiles/python-fastapi/` holds `principles/python-standards.md`,
      `principles/infra-standards.md`, the former `templates/stacks/python-fastapi.md`,
      and `always-on-fragment.md`; `principles/` at the root keeps only
      `code-quality.md` and `testing-standards.md`; the core contains no Python-,
      FastAPI-, or GCP-specific rule
- [ ] `setup-new-project.sh --profile <name>` copies the profile's principles into the
      consumer project's `.ai/principles/` and `.ai/context/`, writes the fragment into
      the project-local `CLAUDE.md` and `AGENTS.md`, and records `name` and source
      `VERSION` in `.ai/profile`; profiles are never deployed as global skills; global
      always-on files stay core-only
- [ ] `README.md` (≤ 120 lines): what it is, who it is for, the 15-minute start
      (`install.sh`, `setup-new-project.sh --profile`, write a spec, `/discovery`), links
      to `docs/USAGE.md`, `docs/SPEC-RUN-QUICKSTART.md`, `docs/reference/`,
      `.ai/specs/README.md`
- [ ] `docs/examples/flat-task/` — the golden `flat` fixture run: spec, Discovery
      artifacts, `state.md` after Execution, PR body, run-log digest
- [ ] `CONTRIBUTING.md`: change flow (spec → `/discovery` → contract check → sync), file
      shape standards, commit rules, how to run tests and the audit prompt
- [ ] `docs/harness-matrix.md` generated from `harness/*/capabilities.md`
- [ ] `--dry-run` for `/discovery` and `/bugfix`
- [ ] The forbidden-token check from spec 00 still passes with its local private pattern
      source; new fixtures use synthetic identifiers, and private patterns are never
      copied into the repository
- [ ] English translations exist alongside every Russian document under `docs/analysis/`
- [ ] Branch protection on `main` (PR required, no direct push); issue and PR templates
      under `.github/`; CI from spec 09
- [ ] The release checklist verifies all criteria and the deferred Apache-2.0 copyright
      holder wording from completed 01; `VERSION` becomes `1.0.0` and tagging/publication
      occur only with explicit owner release authorization

## Out of Scope

- Documentation site (later)
- Renaming the project (completed 01) or the commands (owned by pending 13)

## Notes

- Scrubbing was completed in spec 00 under the amended publication/history decisions
  of ADR-0010; this spec re-verifies the accepted scope without rewriting ancestry.
- Decisions: ADR-0009 Decision 1 (publication, branch protection at release), Decision 6
  (installer, profiles, project-local fragments, `.ai/profile`, examples from fixture,
  translations, scrubbing, owner reviews PRs).
- Depends on specs 01, 09, 10, 13.

## Optimization integration — 2026-10-21

- **REQ-01** THE SYSTEM SHALL document installed optional helpers, context fallbacks,
  actual declared capabilities and disable/resume procedures without claiming planned
  work is shipped. Model-driven examples/benchmarks require spec 09's explicit approval.
- **REQ-02** THE SYSTEM SHALL explain fixed subscription billing versus API-equivalent
  comparisons, unavailable usage/price dimensions and observed versus hypothetical
  savings. It SHALL publish only anonymized synthetic examples, not local transcripts,
  client task context, price credentials or private hygiene patterns.
- **REQ-03** THE SYSTEM SHALL preserve user-edited files during install/uninstall,
  report restore conflicts for owner resolution and test dry-run/backup/restore
  deterministically. Release gates SHALL not initiate paid tests or authorize tagging.

### Acceptance additions

- [ ] **AC-01** (REQ-01, REQ-02) Documentation generated against minimal/full feature
  manifests labels availability and economic evidence correctly; examples contain
  synthetic data and no copied local session content.
- [ ] **AC-02** (REQ-03) Install/uninstall fixtures preserve post-install user changes,
  dry-run writes nothing and release validation cannot run a model or publish a tag.

Dependencies remain 01, 09, 10 and 13. Documentation for optimization features is added
as those features ship; this spec does not require pretending all planned features
already exist. Owner approval of PRs and releases remains separate from this review.
