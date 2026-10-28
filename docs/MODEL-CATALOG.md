# Optional local model catalog

The selector uses a user-owned local catalog and current invocation evidence. It never
executes a model. Ordinary lookup, recommendation and plan resolution are offline;
only explicit workflow `/pd-select-model INPUT --refresh` authorizes source research.
The workflow researches; helper `--refresh CANDIDATE` only validates and installs an
already complete candidate. It never browses or builds a partial catalog.

The canonical plan contract is
[`workflow-reference → Model columns and resolution`](../rules/workflow-reference.md#model-columns-and-resolution).
The public implementations are [the CLI/cache](../scripts/model-catalog.py),
[selection policy](../scripts/model_selection.py) and [plan compatibility](../scripts/model_plan.py).
Python 3.11+ is optional: missing Python, helper or siblings reports selection unavailable
and preserves session configuration. This never authorizes an unverified explicit model
request. An independently eligible, declared authorized fallback or a visible stop is
required before such execution. Without an explicit request, ordinary work can remain
in its current session without claiming selection or a switch.

## Ownership, refresh and recovery

The configuration owner controls catalog evidence, refresh and rollback. The default
path is `$XDG_CONFIG_HOME/orchestrail/model-catalog.md`, or
`~/.config/orchestrail/model-catalog.md` when XDG is unset. `--catalog PATH` overrides it.
Locate the helper through `ORCHESTRAIL_HOME` or a known source checkout; an installed
workflow alone does not prove that the optional helper is installed.

Installed skills do not package this guide beside `SKILL.md`. Follow the canonical
[read-only guidance preflight](../rules/workflow-reference.md#model-columns-and-resolution):
prefer configured `ORCHESTRAIL_HOME`, otherwise use an already-known verified absolute
checkout in invocation-local `SOURCE_ROOT`. Read the helper, its siblings and
`$SOURCE_ROOT/docs/MODEL-CATALOG.md` from the same verified source root. Never infer that
root from CWD or from a per-skill relative link. Relative links in source documents serve
repository readers. Missing helper/guide/schema/rubric reports selection unavailable and
preserves session, plan and catalog; never fabricate scores, schema or refresh candidates.
Required sections are `## Schema and public operations` and
`## Quality rubric, traits and uncertainty`. The preflight only reads files; it installs
no runtime, configuration or documentation. With guidance available, explicit refresh can
still initialize or repair a missing/invalid catalog.

Before an authorized refresh, retain a known-good copy outside the destination. Build a
separate complete candidate from exact provider identifiers, dated availability/context/tool
documentation, independent capability evidence and separate price sources. Invoke:

```text
python3 HELPER --catalog CATALOG --today YYYY-MM-DD --refresh CANDIDATE
```

Validation precedes destination creation and same-directory staging; atomic replacement
installs all bytes together. A validation/write/replacement failure preserves the prior
catalog and reports `Refresh rejected`, even when the old catalog remains usable. Exit 2
means the requested operation failed; do not mistake a usable old catalog for refresh
success. Rollback by passing the retained valid copy as the explicit refresh candidate.
Disable selection by moving the optional catalog aside or declining model-specific routing;
report session-default behavior. No home configuration or installed skill is deployed by
these examples or by validation.

Freshness policy uses calendar days since `refreshed`: 0–13 fresh, 14–30 dated notice,
31 or more stale warning but usable. Over 30 does not trigger automatic browsing.
Missing/malformed/future dates are invalid and selection unavailable. Evidence dates may
not exceed refresh dates. Old but valid evidence is disclosed; it is never transformed
into a fresh capability measurement. Failed research leaves the prior catalog untouched.

## Schema and public operations

Catalog Markdown contains exactly one fenced `json model-catalog` payload and its derived
human tier table. Schema version 1 requires exactly `schema_version`, `refreshed`,
`evidence_date`, `models`; dates use `YYYY-MM-DD`. Every model requires exactly:

| Field | Value |
|---|---|
| `provider`, `id` | `anthropic` or `openai`, and an exact provider identifier |
| `tier` | `light`, `standard`, `frontier`: independent cost/display bands; all three represented |
| `availability` | `available`, `unavailable`, `unknown` |
| `context_window`, `tools` | Positive integer or null; capability-name array or null |
| `traits` | Array containing only `creative`, `heavy-reasoning`, `mechanical` |
| `capability_evidence` | Null, or `{reference,date,quality}` with independent source-supported ordinal quality 1–5 |
| `price_snapshot` | Null, or `{reference,date,relative_cost}` with a positive finite relative price |

Uncalibrated quality is unknown: represent it with `capability_evidence: null`; a non-null
evidence object requires an integer quality, not `quality: null`. Do not convert a name,
price, confidence guess or cost tier into quality. Source-supported ordinal capability
evidence is distinct from a measured success probability. The catalog has no probability
field and no price ledger. Its table header is exactly:

```text
| tier | anthropic model id | openai model id | relative cost |
```

Rows must match the structured payload; do not maintain independent handwritten summaries.
The runnable example below derives its table, uses invented identities and references,
and supplies synthetic evidence only to exercise validation. It is not a real catalog.

Selection JSON requires exactly `scores`, `hard_constraints`, `traits`, `task_class`,
`requirements`, `harness`, `owner`, `default_model`, `cost_comparisons`:

- `scores`: all seven integer signals `C,A,V,R,Ver,Crit,RW`, each 1–5.
- `hard_constraints`: unique names from `security`, `financial`, `architecture`,
  `core-invariant`, `high-blast-radius`.
- `requirements`: `{context_tokens,tools}`. `owner`: `{allowed_models,excluded_models}`;
  allowed models may be null. Model identities are `{provider,id}` everywhere.
- `harness`: `{reference,date,models}` with each model exactly
  `{provider,id,availability,context_window,tools}`. Observe it afresh for this invocation
  from the actual exposed tool and current permissions/restrictions. `date` must equal
  today; that date/reference does not itself authenticate the caller's observation.
- `default_model`: known session identity or null. `cost_comparisons`: explicit owner
  exports or `[]`; empty comparisons retain a suitable default.

Do not infer support from catalog TTL, a provider/harness name, a logging capability file,
or successful dispatch. Permissions and restrictions can change within a catalog's lifetime
or within one day. Unknown support/context/tools excludes a model-specific request.

```text
python3 HELPER --catalog CATALOG --today YYYY-MM-DD
python3 HELPER --catalog CATALOG --today YYYY-MM-DD --select REQUEST.json
python3 HELPER --read-plan PLAN --provider openai
python3 HELPER --update-plan PLAN --updates UPDATES.json
python3 HELPER --catalog CATALOG --today YYYY-MM-DD --resolve-plan PLAN --provider openai --row ROW --resolution RESOLUTION.json
```

Read/update do not accept `--catalog` or `--today`; resolution does. `UPDATES.json` maps
row IDs to provider keys and exact IDs or intentional null. Provider columns are
`Model (Claude)` and `Model (Codex)`; a present empty active column overrides legacy
`Model`. Adding columns to populated legacy rows requires explicit decisions for every
new provider on every such row. Never infer cross-provider aliases. Preserve unrelated
bytes, statuses and composite blanks. Scope changes invalidate populated recommendations;
single mode does not repair persisted cells.

`RESOLUTION.json` contains exactly `{selection,fallback,execution}`; `selection` is the
selection input above, `fallback` is `{authorized,model}`, and `execution` stays null
during recommendation/resolution. The helper derives provider/requested identity from
the selected plan row. Reports distinguish requested, resolved and actual; status is
`resolved`, `session-default`, `fallback`, `stopped` or `unavailable`. Successful operations
exit 0; rejection/unavailable/stopped exit 2. Structural CLI misuse is an argparse error.

Actual remains unknown without a separately observed current execution receipt
`{model,reference,date}` matching the authorized resolved provider/ID and current worker/task.
The caller owns receipt provenance. The helper validates matching fields; it cannot
authenticate a receipt. Plan cells, recommendations, spawn arguments and successful spawn
requests are insufficient. Never synthesize execution evidence or claim these examples ran
a model. An inline executor preserves its session because it cannot switch itself.

## Quality rubric, traits and uncertainty

| Score | C complexity | A ambiguity | V context | R subtle errors | Ver verification | Crit blast radius | RW rework |
|---|---|---|---|---|---|---|---|
| 1 | Obvious operation | Fully specified | One file | Immediately obvious | Production needed | Cosmetic | Minutes |
| 2 | Familiar small logic | Inferable gap | A few files | First-run visible | Deep review/staging | Local tooling | Under an hour |
| 3 | Branching edge cases | Judgment needed | Module | Casual review misses | New tests/manual check | User-facing | Hours/dependent |
| 4 | Cross-module invariants | Conflicting requirements | System | Plausible wrong result | Existing tests detect | Auth/data adjacent | Day/dependents |
| 5 | System design | Undefined intent | External/system | Silent corruption | Compiler/linter detects | Finance/security/core | Redesign |

Round half up `0.25*C + 0.20*A + 0.15*V + 0.20*R + 0.20*Crit`; add one for RW=5,
subtract one for Ver=5, then clamp to independent ordinal quality 1–5. Any mandatory
hard category sets quality floor 5. Demand labels Light/Standard/Frontier may summarize
scores for display but never establish model eligibility or equate cost with quality.
Raising risk/ambiguity/context/criticality/rework or lowering verifiability cannot lower
the floor. Creative specialization never bypasses that floor.

Trait migration: `long-context` → `heavy-reasoning`; `coding-heavy` → `heavy-reasoning`;
`web-knowledge` → `heavy-reasoning`; `cost-efficient-bulk` → `mechanical`;
`general` and `general (default)` → no trait (empty array); `creative` remains creative.
Creative and heavy-reasoning may coexist. Mechanical conflicts with either; general
cannot be combined with specialization. Legacy names never replace explicit context/tool
requirements, and unknown/conflicting traits are rejected.

Filter availability, current support, context, tools, owner limits, quality and traits
before economics. Keep a suitable default; absent one, choose the strongest eligible
baseline. Equal quality and token prices do not establish equivalent-task expected cost.
`price_snapshot` never displaces a default. Unknown prices or calibration stay unknown.

The calibration owner supplies curated comparable expected-total-cost evidence, separately
from price snapshots. Each `cost_comparisons` entry requires exactly `reference`, `date`,
`qualification: "comparable-task-evaluation"`, `task_class`, `quality_floor`, `traits`,
`requirements`, `currency`, `estimates`; estimates contain provider/ID plus
`total_cost_lower`/`total_cost_upper` as nonnegative decimal strings. Workload/result quality,
traits and requirements must cover the request, and baseline cost must be present. Only an
unambiguous nonoverlapping cheaper interval can justify displacement. Equal, overlapping,
conflicting, incomplete or unqualified evidence retains the suitable baseline with reasons.
The selector performs no paid evaluation or invented probability/ECE calculation.

Telemetry has a separate owner; existing instrumentation and retrospective workflows own
its collection/interpretation. Historical stores must not be read by the selector or plan
resolver. Only explicitly supplied curated exports cross that boundary; these helpers never
discover, repair, write or calibrate from historical logs. Calibration ownership remains
external until comparable evidence has been reviewed; no production default changes here.

## Executable offline CLI examples

Run the block from any directory with `ORCHESTRAIL_HOME` pointing to a source checkout.
It creates and cleans a temporary workspace and isolated home/config/state/log roots.
The date, identities, evidence and relative prices are fictional. The small wrapper only
translates genuinely missing local dependencies into the caller's unavailable report;
all available-helper reports come from actual public CLI operations. Rejected operations
are inspected without aborting the example. No provider, model or historical store is used.

```bash model-catalog-example
python3 - <<'PY'
from __future__ import annotations

from copy import deepcopy
from datetime import date
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
from time import perf_counter
from typing import Any

# Any represents heterogeneous fictional JSON and the dynamically loaded public API.
# The real helper validates these inputs; no report is invented for an available helper.
TODAY = "2032-06-15"


def identity(name: str) -> dict[str, str]:
    return {"provider": "openai", "id": name}


def markdown(payload: dict[str, Any]) -> str:
    lines = ["# Fictional catalog", "", "```json model-catalog", json.dumps(payload), "```", "",
             "| tier | anthropic model id | openai model id | relative cost |", "|---|---|---|---|"]
    for model in payload["models"]:
        snapshot = model["price_snapshot"]
        cost = format(snapshot["relative_cost"], "g") if snapshot else "unknown"
        lines.append(f"| {model['tier']} | - | {model['id']} | {model['id']}={cost} |")
    return "\n".join(lines) + "\n"


def run(arguments: list[str], overrides: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    settings = overrides or {}
    runtime = settings.get("python", sys.executable)
    command = Path(settings.get("helper", str(helper)))
    missing = []
    if shutil.which(runtime) is None:
        missing.append(f"Python unavailable: {runtime}")
    if not command.is_file():
        missing.append(f"Helper unavailable: {command}")
    if missing:
        return 2, {"status": "unavailable", "session_action": "preserve", "errors": missing,
                   "resolved": None, "actual": None, "notice": "Catalog selection unavailable"}
    result = subprocess.run([runtime, str(command), *arguments], env=environment,
                            capture_output=True, text=True, check=False, timeout=10)
    return result.returncode, json.loads(result.stdout)


def emit(name: str, result: tuple[int, dict[str, Any]], extra: dict[str, Any] | None = None) -> None:
    print(json.dumps({"example": name, "exit_code": result[0], "report": result[1], **(extra or {})}))


def resolve(document: Path, request: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    resolution_path.write_text(json.dumps(request))
    return run(["--catalog", str(catalog_path), "--today", TODAY, "--resolve-plan", str(document),
                "--provider", "openai", "--row", "build", "--resolution", str(resolution_path)])


with tempfile.TemporaryDirectory(prefix="catalog-guide-") as temporary:
    workspace = Path(temporary)
    helper = Path(os.environ["ORCHESTRAIL_HOME"]) / "scripts/model-catalog.py"
    environment = dict(os.environ, HOME=str(workspace / "home"),
                       XDG_CONFIG_HOME=str(workspace / "config"),
                       XDG_STATE_HOME=str(workspace / "state"),
                       ORCHESTRAIL_LOG_ROOT=str(workspace / "logs"))
    models = []
    for name, tier, quality in (("fixture-small", "light", 2), ("fixture-middle", "standard", 3),
                                ("fixture-strong", "frontier", 5)):
        models.append({**identity(name), "tier": tier, "availability": "available",
                       "context_window": 64000, "tools": ["read", "shell"], "traits": [],
                       "capability_evidence": {"reference": f"fictional-quality:{name}",
                                               "date": TODAY, "quality": quality},
                       "price_snapshot": {"reference": f"fictional-price:{name}",
                                          "date": TODAY, "relative_cost": quality}})
    payload = {"schema_version": 1, "refreshed": TODAY, "evidence_date": TODAY, "models": models}
    candidate = workspace / "candidate.md"
    candidate.write_text(markdown(payload))
    catalog_path = workspace / "cache/catalog.md"
    emit("refresh", run(["--catalog", str(catalog_path), "--today", TODAY, "--refresh", str(candidate)]))
    emit("inspect", run(["--catalog", str(catalog_path), "--today", TODAY]))
    previous = catalog_path.read_bytes()
    invalid = workspace / "invalid.md"
    invalid.write_text("Incomplete fictional candidate\n")
    rejected = run(["--catalog", str(catalog_path), "--today", TODAY, "--refresh", str(invalid)])
    emit("refresh-rejected", rejected, {"catalog_bytes_unchanged": catalog_path.read_bytes() == previous})

    selection = {"scores": {factor: 2 for factor in ("C", "A", "V", "R", "Ver", "Crit", "RW")},
                 "hard_constraints": [], "traits": [], "task_class": "fictional-equivalent-work",
                 "requirements": {"context_tokens": 8000, "tools": ["read", "shell"]},
                 "harness": {"reference": "fictional-current-invocation", "date": TODAY,
                             "models": [{**identity(model["id"]), "availability": "available",
                                         "context_window": 64000, "tools": ["read", "shell"]}
                                        for model in models]},
                 "owner": {"allowed_models": None, "excluded_models": []},
                 "default_model": identity("fixture-strong"), "cost_comparisons": []}
    selection_path = workspace / "selection.json"
    selection_path.write_text(json.dumps(selection))
    emit("select", run(["--catalog", str(catalog_path), "--today", TODAY, "--select", str(selection_path)]))

    legacy = workspace / "legacy.md"
    original = ("# Fictional plan\n\n## Subtasks\n\n"
                "| ID | Name | Model | Status | Extra |\n|---|---|---|---|---|\n"
                "| build | Build | fixture-middle | not-started | keep-build |\n"
                "| audit | Audit | fixture-middle | done | keep-audit |\n"
                "| group | Container | | not-started | keep-container |\n\n"
                "## Notes\n\nPreserve these unrelated bytes and trailing spaces.  \n")
    legacy.write_text(original)
    emit("read-legacy", run(["--read-plan", str(legacy), "--provider", "openai"]))
    dual = workspace / "dual.md"
    dual.write_text("## Subtasks\n\n| ID | Model | Model (Claude) | Model (Codex) | Status |\n"
                    "|---|---|---|---|---|\n| build | fixture-absent | | | not-started |\n")
    emit("read-dual-empty", run(["--read-plan", str(dual), "--provider", "openai"]))
    missing = workspace / "missing-columns.md"
    missing.write_text("## Subtasks\n\n| ID | Status |\n|---|---|\n| build | not-started |\n")
    emit("read-missing", run(["--read-plan", str(missing), "--provider", "openai"]))
    updates_path = workspace / "updates.json"
    updates_path.write_text(json.dumps({"build": {"anthropic": None, "openai": "fixture-middle"}}))
    rejected = run(["--update-plan", str(legacy), "--updates", str(updates_path)])
    emit("migration-rejected", rejected, {"plan_bytes_unchanged": legacy.read_text() == original})
    updates_path.write_text(json.dumps({"build": {"anthropic": None, "openai": "fixture-middle"},
                                       "audit": {"anthropic": None, "openai": None}}))
    updated = run(["--update-plan", str(legacy), "--updates", str(updates_path)])
    before_lines, after_lines = original.splitlines(), legacy.read_text().splitlines()
    preserved = len(before_lines) == len(after_lines) and all(
        after.startswith(before) for before, after in zip(before_lines, after_lines))
    emit("update", updated, {"unrelated_bytes_preserved": preserved})

    resolution_path = workspace / "resolution.json"
    request = {"selection": selection, "fallback": {"authorized": False, "model": None}, "execution": None}
    emit("resolve-requested", resolve(legacy, request))
    absent = workspace / "absent-request.md"
    absent.write_text("## Subtasks\n\n| ID | Model | Status |\n|---|---|---|\n"
                      "| build | fixture-absent | not-started |\n")
    emit("resolve-stop", resolve(absent, request))
    fallback = deepcopy(request)
    fallback["fallback"] = {"authorized": True, "model": identity("fixture-strong")}
    emit("resolve-fallback", resolve(absent, fallback))
    emit("resolve-default", resolve(dual, request))
    restricted = deepcopy(request)
    restricted["selection"]["harness"]["models"][1]["tools"] = ["read"]
    emit("restricted-tools", resolve(legacy, restricted))
    stale = deepcopy(request)
    stale["selection"]["harness"]["date"] = "2032-06-14"
    emit("stale-support", resolve(legacy, stale))

    unknown = deepcopy(payload)
    unknown["models"][1]["capability_evidence"] = None
    unknown_path = workspace / "unknown-quality.md"
    unknown_path.write_text(markdown(unknown))
    emit("unknown-quality", run(["--catalog", str(unknown_path), "--today", TODAY,
                                 "--select", str(selection_path)]))
    run(["--today", TODAY, "--refresh", str(candidate)])
    emit("default-path", run(["--today", TODAY]))
    emit("missing-catalog", run(["--catalog", str(workspace / "absent.md"), "--today", TODAY]))
    emit("missing-helper", run([], {"helper": str(workspace / "missing-helper.py")}))
    emit("missing-python", run([], {"python": str(workspace / "missing-python")}))

    api = runpy.run_path(str(helper), run_name="fictional_guide_api")
    started = perf_counter()
    for _ in range(100):
        report = api["inspect_catalog"](catalog_path, date.fromisoformat(TODAY))
        assert report["selection_available"], report
    elapsed = perf_counter() - started
    print(json.dumps({"example": "warm-fixture-latency", "iterations": 100,
                      "elapsed_seconds": elapsed, "live_selection_measured": False}))
PY
```

## Validation and timing limits

Run `bash scripts/validate-contracts.sh --model-workflow-only` for the same catalog,
selection, plan, workflow and instruction suites registered in default validation.
The fixtures check strict schema/table drift, date boundaries, atomic rejection,
scoring boundaries/monotonicity, compatible plans, current support, uncertainty and
reference reachability. Executable examples run under a Python network guard with
disposable configuration; no real catalog, historical logs or paid comparisons are read.

The executable block reports measured fictional-fixture warm lookup latency over 100
in-process `inspect_catalog` calls. It excludes CLI startup, research and model execution.
One local validation run on 2026-10-28 measured those 100 calls in 0.044275 seconds;
the example prints a new measurement on every run rather than reusing that value.
The focused gate requires the measured batch below one second. A live 60-second selection
target remains a target; live selection is unmeasured. No savings measurement or claim is
made. Observing a fixture measurement does not establish faster live routing or quality.
