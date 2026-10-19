# Open-source readiness: installer, profiles, examples, scrubbing, contributing

## Goal

After spec 01 the repository is public but still shaped for one machine: `sync.sh`
overwrites the user's global files without asking, the Python/FastAPI/GCP standards are
the default for everyone, client project names appear in the knowledge base, and there
is no example of a finished task or a contribution guide. Make Orchestrail installable
by a stranger in fifteen minutes and technology-neutral at its core (ADR-0009,
Decisions 1 and 6).

## Acceptance Criteria

- [ ] `install.sh` replaces `sync.sh` for external users: `--dry-run` lists every path it
      would write; a backup of an existing `~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md`
      is taken before overwrite; `--uninstall` removes every path listed in the skill
      manifest and restores the backups; `sync.sh` remains the maintainer's deploy
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
- [ ] The forbidden-token check from spec 00 still passes, and the denylist is extended
      with anything introduced since (profile fragments, examples, README)
- [ ] English translations exist alongside every Russian document under `docs/analysis/`
- [ ] Branch protection on `main` (PR required, no direct push); issue and PR templates
      under `.github/`; CI from spec 09
- [ ] `VERSION` bumped to `1.0.0` and tagged when every criterion above holds

## Out of Scope

- Documentation site (later)
- Renaming the project (done in spec 01) or the commands (done in spec 13)

## Notes

- Scrubbing of client names was moved to spec 00 and completed before the first commit;
  this spec only re-verifies it.
- Decisions: ADR-0009 Decision 1 (publication, branch protection at release), Decision 6
  (installer, profiles, project-local fragments, `.ai/profile`, examples from fixture,
  translations, scrubbing, owner reviews PRs).
- Depends on specs 01, 09, 10, 13.
