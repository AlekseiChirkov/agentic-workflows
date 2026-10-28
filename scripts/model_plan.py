"""Read compatible plan columns, update explicitly, and resolve without executing models.

Public API: read_plan(markdown, provider), update_plan(markdown, updates),
write_plan(path, updates), resolve_model(catalog, request, today). Providers are
anthropic/openai; their columns are Model (Claude)/Model (Codex). A present active
column wins even when empty; legacy Model applies only when that column is absent.
Empty cells and -/— mean session default. Models are exact identifiers, never aliases.

Updates map row IDs to provider:null|exact-id objects. Nonempty updates add both
optional columns. Every nonempty legacy row needs explicit values for newly added
columns; otherwise migration would silently turn legacy requests into defaults.
Unchanged cells, unrelated Markdown, newline style and final-newline state survive.

Resolution request={provider,requested:null|identity,selection,fallback,execution}.
Selection is the public selection policy request; economics do not route requests.
Fallback={authorized:bool,model:null|identity}; execution=null|{model,reference,date}.
Only a separate current-day receipt matching the authorized resolution sets actual.
The caller supplies that observation; this helper neither executes nor measures it.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import os
from pathlib import Path
import re
import runpy
import tempfile
from typing import Any

# Any represents heterogeneous, untrusted JSON and runpy exports at public boundaries.
# Explicit validators establish structures and scalar types before use.
COLUMNS = {"anthropic": "Model (Claude)", "openai": "Model (Codex)"}
SELECT_MODEL = runpy.run_path(str(Path(__file__).with_name("model_selection.py")),
                             run_name="plan_selection_policy")["select_model"]


@dataclass(frozen=True)
class PlanTable:
    """Validated row coordinates retain the caller's original Markdown bytes."""

    lines: list[str]
    header: int
    columns: list[str]
    row_lines: list[int]
    rows: list[list[str]]


def _object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label}: expected exactly {', '.join(sorted(keys))}")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(ord(char) < 32 for char in value):
        raise ValueError(f"{label}: expected nonempty text without control characters")
    return value


def _provider(provider: Any) -> str:
    if not isinstance(provider, str) or provider not in COLUMNS:
        raise ValueError("provider: expected anthropic or openai")
    return provider


def _model(value: Any) -> str | None:
    if value is None or (isinstance(value, str) and value in ("", "-", "—")):
        return None
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]*", value):
        raise ValueError("model: expected an exact identifier without whitespace or Markdown delimiters")
    return value


def _identity(value: Any, provider: str) -> dict[str, str] | None:
    if value is None:
        return None
    model = _object(value, {"provider", "id"}, "model identity")
    if _provider(model["provider"]) != provider:
        raise ValueError("model identity: provider switching is not supported")
    name = _model(model["id"])
    if name is None:
        raise ValueError("model identity: expected an exact nonempty identifier")
    return {"provider": provider, "id": name}


def _visible(lines: list[str]) -> list[tuple[int, str]]:
    visible: list[tuple[int, str]] = []
    fence: str | None = None
    for index, line in enumerate(lines):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*?)[\r\n]*$", line)
        if fence is not None:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
        elif marker:
            fence = marker[1]
        elif not line.startswith(("    ", "\t")):
            visible.append((index, line))
    return visible


def _section(lines: list[str]) -> list[tuple[int, str]]:
    visible = _visible(lines)
    headings = [(index, re.fullmatch(r" {0,3}##[ \t]+Subtasks[ \t]*#*[ \t]*[\r\n]*", line))
                for index, line in visible]
    starts = [index for index, match in headings if match]
    if len(starts) != 1:
        raise ValueError("plan: expected exactly one unfenced Subtasks section")
    selected = []
    for index, line in visible:
        if index <= starts[0]:
            continue
        if re.match(r"^ {0,3}#{1,2}(?:[ \t]|$)", line):
            break
        selected.append((index, line))
    return selected


def _pipes(line: str) -> list[int]:
    positions = []
    backslashes = 0
    for index, char in enumerate(line):
        if char == "|" and backslashes % 2 == 0:
            positions.append(index)
        backslashes = backslashes + 1 if char == "\\" else 0
    return positions


def _cells(line: str) -> list[str]:
    body = line.rstrip("\r\n")
    positions = _pipes(body)
    if (len(positions) < 2 or body[:positions[0]].strip() or body[positions[-1] + 1:].strip()):
        raise ValueError("plan table: rows must have unescaped opening and closing pipes")
    return [body[left + 1:right].strip() for left, right in zip(positions, positions[1:])]


def _table_lines(lines: list[str]) -> list[int]:
    groups: list[list[int]] = []
    for index, line in _section(lines):
        if not line.lstrip().startswith("|"):
            if groups and index == groups[-1][-1] + 1 and _pipes(line):
                raise ValueError("plan table: malformed row boundary")
            continue
        if not groups or index != groups[-1][-1] + 1:
            groups.append([])
        groups[-1].append(index)
    if len(groups) != 1 or len(groups[0]) < 2:
        raise ValueError("plan: expected exactly one unambiguous subtask table")
    return groups[0]


def _validated_rows(table: PlanTable) -> None:
    seen: set[str] = set()
    for cells in table.rows:
        if len(cells) != len(table.columns):
            raise ValueError("plan table: ragged row")
        row_id = _text(cells[table.columns.index("ID")], "row ID")
        _text(cells[table.columns.index("Status")], "row status")
        if row_id in seen:
            raise ValueError("plan table: duplicate row ID")
        seen.add(row_id)
        for column in ("Model", *COLUMNS.values()):
            if column in table.columns:
                _model(cells[table.columns.index(column)])


def _parse(markdown: str) -> PlanTable:
    if not isinstance(markdown, str):
        raise ValueError("plan: expected Markdown text")
    lines = markdown.splitlines(keepends=True)
    indices = _table_lines(lines)
    columns, separator = _cells(lines[indices[0]]), _cells(lines[indices[1]])
    if (not all(columns) or len(set(columns)) != len(columns)
            or not {"ID", "Status"} <= set(columns)):
        raise ValueError("plan table: require unique headers including ID and Status")
    if len(separator) != len(columns) or any(not re.fullmatch(r":?-{3,}:?", cell) for cell in separator):
        raise ValueError("plan table: malformed Markdown separator")
    table = PlanTable(lines, indices[0], columns, indices[2:], [_cells(lines[index]) for index in indices[2:]])
    _validated_rows(table)
    return table


def read_plan(markdown: str, provider: str) -> list[dict[str, Any]]:
    """Read ordered exact requests; an empty present provider cell never uses legacy."""
    active = COLUMNS[_provider(provider)]
    table = _parse(markdown)
    source = active if active in table.columns else "Model" if "Model" in table.columns else "session-default"
    result = []
    for cells in table.rows:
        name = None if source == "session-default" else _model(cells[table.columns.index(source)])
        result.append({"id": cells[table.columns.index("ID")], "status": cells[table.columns.index("Status")],
                       "source": source, "requested": None if name is None else {"provider": provider, "id": name}})
    return result


def _updates(value: Any, table: PlanTable) -> dict[str, dict[str, str | None]]:
    if not isinstance(value, dict):
        raise ValueError("updates: expected row IDs mapped to provider/model objects")
    identifiers = {row[table.columns.index("ID")] for row in table.rows}
    result: dict[str, dict[str, str | None]] = {}
    for row_id, models in value.items():
        if not isinstance(row_id, str) or row_id not in identifiers:
            raise ValueError("updates: unknown row ID")
        if not isinstance(models, dict):
            raise ValueError("updates: expected provider/model object")
        result[row_id] = {_provider(provider): _model(name) for provider, name in models.items()}
    return result


def _migration(table: PlanTable, updates: dict[str, dict[str, str | None]]) -> list[str]:
    added = [provider for provider, column in COLUMNS.items() if column not in table.columns]
    if "Model" not in table.columns:
        return added
    for cells in table.rows:
        if _model(cells[table.columns.index("Model")]) is None:
            continue
        row_id = cells[table.columns.index("ID")]
        if any(provider not in updates.get(row_id, {}) for provider in added):
            raise ValueError("legacy migration: supply an explicit value for every newly added provider column")
    return added


def _replace_cell(raw: str, value: str) -> str:
    leading = raw[:len(raw) - len(raw.lstrip())]
    trailing = raw[len(raw.rstrip()):]
    return leading + value + trailing if raw.strip() else " " + value + " "


def _edited_line(line: str, edits: dict[int, str], additions: list[str]) -> str:
    positions = _pipes(line)
    pieces = [line[:positions[0] + 1]]
    for index, (left, right) in enumerate(zip(positions, positions[1:])):
        raw = line[left + 1:right]
        pieces.append(_replace_cell(raw, edits[index]) if index in edits else raw)
        pieces.append("|")
    pieces.extend(" " + value + " |" for value in additions)
    pieces.append(line[positions[-1] + 1:])
    return "".join(pieces)


def _updated_rows(table: PlanTable, updates: dict[str, dict[str, str | None]], added: list[str]) -> None:
    for index, cells in zip(table.row_lines, table.rows):
        models = updates.get(cells[table.columns.index("ID")], {})
        edits = {table.columns.index(COLUMNS[provider]): name or "" for provider, name in models.items()
                 if COLUMNS[provider] in table.columns and _model(cells[table.columns.index(COLUMNS[provider])]) != name}
        additions = [models.get(provider) or "" for provider in added]
        if edits or added:
            table.lines[index] = _edited_line(table.lines[index], edits, additions)


def update_plan(markdown: str, updates: dict[str, Any]) -> str:
    """Validate the whole table and update before returning preserved Markdown."""
    table = _parse(markdown)
    checked = _updates(updates, table)
    if not any(checked.values()):
        return markdown
    added = _migration(table, checked)
    if added:
        table.lines[table.header] = _edited_line(table.lines[table.header], {}, [COLUMNS[key] for key in added])
        table.lines[table.header + 1] = _edited_line(table.lines[table.header + 1], {}, ["---"] * len(added))
    _updated_rows(table, checked, added)
    result = "".join(table.lines)
    _parse(result)
    return result


def _atomic_write(path: Path, content: bytes) -> None:
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", prefix=".model-plan-", suffix=".tmp",
                                         dir=path.parent, delete=False) as staging:
            temporary = Path(staging.name)
            staging.write(content)
            staging.flush()
            os.fsync(staging.fileno())
        os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_plan(path: Path, updates: dict[str, Any]) -> bool:
    """Atomically replace an explicitly named existing plan only after full validation."""
    path = Path(path)
    before = path.read_bytes()
    after = update_plan(before.decode("utf-8"), updates).encode("utf-8")
    if before == after:
        return False
    _atomic_write(path, after)
    return True


def _resolution_request(request: dict[str, Any]) -> dict[str, Any]:
    checked = _object(request, {"provider", "requested", "selection", "fallback", "execution"}, "resolution request")
    provider = _provider(checked["provider"])
    _identity(checked["requested"], provider)
    fallback = _object(checked["fallback"], {"authorized", "model"}, "fallback")
    if type(fallback["authorized"]) is not bool:
        raise ValueError("fallback.authorized: expected boolean")
    _identity(fallback["model"], provider)
    if not isinstance(checked["selection"], dict):
        raise ValueError("selection: expected public selection request")
    return checked


def _actual(evidence: Any, resolved: dict[str, str] | None, today: date) -> dict[str, str] | None:
    if evidence is None:
        return None
    receipt = _object(evidence, {"model", "reference", "date"}, "execution")
    _text(receipt["reference"], "execution.reference")
    if receipt["date"] != today.isoformat():
        raise ValueError("execution.date: require a separate current-day execution receipt")
    if resolved is None or _identity(receipt["model"], resolved["provider"]) != resolved:
        raise ValueError("execution.model: evidence must match the authorized resolved identity")
    return dict(resolved)


def _reasons(candidate: dict[str, str] | None, policy: dict[str, Any]) -> list[str]:
    if candidate is None:
        return ["session-default-unknown"]
    for excluded in policy["excluded"]:
        if all(excluded[key] == candidate[key] for key in ("provider", "id")):
            return list(excluded["reasons"])
    return ["catalog-unlisted"]


def _resolved(request: dict[str, Any], policy: dict[str, Any]) -> tuple[str, dict[str, str] | None, list[str]]:
    requested = request["requested"]
    candidate = requested if requested is not None else _identity(
        request["selection"]["default_model"], request["provider"])
    if candidate is not None and candidate in policy["eligible"]:
        return ("resolved" if requested is not None else "session-default"), candidate, ["all-eligibility-constraints-satisfied"]
    reasons = _reasons(candidate, policy)
    fallback = request["fallback"]
    if fallback["authorized"] and fallback["model"] is not None and fallback["model"] in policy["eligible"]:
        return "fallback", fallback["model"], reasons + ["authorized-declared-fallback"]
    if fallback["model"] is not None:
        reasons += ["fallback-unauthorized"] if not fallback["authorized"] else ["fallback-ineligible", *_reasons(fallback["model"], policy)]
    return "stopped", None, reasons


def resolve_model(catalog: dict[str, Any], request: dict[str, Any], today: date) -> dict[str, Any]:
    """Resolve only the exact request/default or a declared authorized suitable fallback."""
    checked = _resolution_request(request)
    selection = dict(checked["selection"], cost_comparisons=[])
    policy = SELECT_MODEL(catalog, selection, today)
    status, resolved, reasons = _resolved(checked, policy)
    return {"status": status, "requested": checked["requested"], "resolved": resolved,
            "actual": _actual(checked["execution"], resolved, today), "reasons": reasons,
            "quality_floor": policy["quality_floor"], "eligible": policy["eligible"], "excluded": policy["excluded"]}
