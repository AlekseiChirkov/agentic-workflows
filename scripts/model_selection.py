"""Pure conservative recommendations over a validated local catalog and explicit evidence.

Public API: quality_floor(scores, hard_constraints=()), normalize_traits(traits),
select_model(catalog, request, today). Selection never executes a model or reads a file.
Catalog input is the schema-version-1 payload returned by validate_catalog/inspect_catalog.
The request supplies exact provider/id identities, current harness support, owner limits,
requirements and a default; omitted economics cannot displace a suitable default.
The caller observes harness support afresh for each invocation: harness.date must equal
today. Catalog freshness and historical comparable-task evaluation dates do not authorize
requestability; neither substitutes for this current-invocation capability snapshot.

Cost comparisons are optional caller-owned comparable-task evaluation exports, not token
prices or inferred success rates. Each records provenance, date, task/result-quality scope,
currency and externally qualified total-cost intervals. Only disjoint intervals justify a
change. These inputs are neither persisted nor interpreted as observed execution identity.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
import re
from typing import Any, TypeAlias

# Any represents heterogeneous, untrusted JSON at these public boundaries. Explicit
# validators below check required structures and scalar types before policy evaluation.

SIGNAL_WEIGHTS = {"C": 25, "A": 20, "V": 15, "R": 20, "Ver": 0, "Crit": 20, "RW": 0}
HARD_CONSTRAINTS = ("security", "financial", "architecture", "core-invariant", "high-blast-radius")
TRAITS = ("creative", "heavy-reasoning", "mechanical")
LEGACY_TRAITS = {"general": None, "general (default)": None, "creative": "creative",
                 "long-context": "heavy-reasoning", "coding-heavy": "heavy-reasoning",
                 "web-knowledge": "heavy-reasoning", "cost-efficient-bulk": "mechanical"}
REQUEST_KEYS = {"scores", "hard_constraints", "traits", "task_class", "requirements",
                "harness", "owner", "default_model", "cost_comparisons"}
Identity: TypeAlias = tuple[str, str]
CostIntervals: TypeAlias = dict[Identity, tuple[Decimal, Decimal]]


@dataclass(frozen=True)
class SelectionContext:
    """Validated task inputs shared by the ordered selection stages."""

    request: dict[str, Any]
    floor: int
    traits: list[str]
    requirements: dict[str, Any]
    snapshot: dict[Identity, dict[str, Any]]
    owner: dict[str, Any]
    default: Identity | None
    today: date


def _object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label}: expected exactly {', '.join(sorted(keys))}")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(ord(char) < 32 for char in value):
        raise ValueError(f"{label}: expected a nonempty source or name without control characters")
    return value


def _date(value: Any, today: date, label: str) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"{label}: expected YYYY-MM-DD")
    result = date.fromisoformat(value)
    if result > today:
        raise ValueError(f"{label}: future evidence is unavailable")
    return result


def _strings(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not re.fullmatch(
            r"[a-z][a-z0-9-]*", item) for item in value):
        raise ValueError(f"{label}: expected capability names as a string array")
    if len(value) != len(set(value)):
        raise ValueError(f"{label}: duplicates are not supported")
    return value


def _identity(value: Any) -> Identity:
    model = _object(value, {"provider", "id"}, "model identity")
    if model["provider"] not in ("anthropic", "openai"):
        raise ValueError("model identity: unsupported provider")
    if not isinstance(model["id"], str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]*", model["id"]):
        raise ValueError("model identity: expected an exact nonempty identifier")
    return model["provider"], model["id"]


def _identity_list(value: Any) -> list[Identity]:
    if not isinstance(value, list):
        raise ValueError("model identities: expected an array")
    result = [_identity(item) for item in value]
    if len(result) != len(set(result)):
        raise ValueError("model identities: duplicate provider/id")
    return result


def _display(identity: Identity) -> dict[str, str]:
    return {"provider": identity[0], "id": identity[1]}


def quality_floor(scores: dict[str, int], hard_constraints: list[str] | tuple[str, ...] = ()) -> int:
    """Map all seven integer signals to ordinal quality 1..5 with integer rounding.

    Ver=1 means difficult/late verification; Ver=5 means cheap/immediate verification.
    The weighted demand is rounded half up, raised for RW=5, lowered for Ver=5,
    then clamped. Mandatory categories always require independently evidenced quality 5.
    Cost bands are display groups and never participate in this calculation.
    """
    if not isinstance(scores, dict) or set(scores) != set(SIGNAL_WEIGHTS):
        raise ValueError("scores: expected exactly C, A, V, R, Ver, Crit, RW")
    if any(type(score) is not int or not 1 <= score <= 5 for score in scores.values()):
        raise ValueError("scores: each signal must be an integer 1..5, excluding booleans")
    if (not isinstance(hard_constraints, (tuple, list)) or any(
            not isinstance(item, str) or item not in HARD_CONSTRAINTS for item in hard_constraints)
            or len(hard_constraints) != len(set(hard_constraints))):
        raise ValueError("hard_constraints: expected unique supported category names")
    weighted = (sum(scores[factor] * weight for factor, weight in SIGNAL_WEIGHTS.items()) + 50) // 100
    adjusted = weighted + (scores["RW"] == 5) - (scores["Ver"] == 5)
    return 5 if hard_constraints else max(1, min(5, adjusted))


def normalize_traits(traits: list[str]) -> list[str]:
    """Normalize explicit traits and legacy labels without overriding any floor.

    general/general (default) -> no specialization; coding-heavy/long-context/
    web-knowledge -> heavy-reasoning; cost-efficient-bulk -> mechanical;
    creative -> creative. Creative and heavy-reasoning may coexist. Mechanical
    conflicts with either; a general label conflicts with any specialization.
    Legacy labels describe specialization only: context/tools remain explicit requirements.
    """
    if not isinstance(traits, list) or any(not isinstance(item, str) for item in traits):
        raise ValueError("traits: expected a string array")
    if len(traits) != len(set(traits)):
        raise ValueError("traits: duplicate label")
    converted: set[str] = set()
    is_general = False
    for trait in traits:
        if trait in TRAITS:
            converted.add(trait)
        elif trait in LEGACY_TRAITS:
            mapped = LEGACY_TRAITS[trait]
            if mapped is None:
                is_general = True
            else:
                converted.add(mapped)
        else:
            raise ValueError(f"traits: unknown label {trait}")
    if (is_general and converted) or ("mechanical" in converted and len(converted) > 1):
        raise ValueError("traits: conflicting specialization labels")
    return [trait for trait in TRAITS if trait in converted]


def _requirements(value: Any) -> dict[str, Any]:
    requirements = _object(value, {"context_tokens", "tools"}, "requirements")
    if type(requirements["context_tokens"]) is not int or requirements["context_tokens"] <= 0:
        raise ValueError("requirements.context_tokens: expected a positive integer")
    _strings(requirements["tools"], "requirements.tools")
    return requirements


def _limits(model: dict[str, Any]) -> None:
    context = model["context_window"]
    if context is not None and (type(context) is not int or context <= 0):
        raise ValueError("context_window: expected a positive integer or null")
    if model["tools"] is not None:
        _strings(model["tools"], "tools")
    if not isinstance(model["availability"], str) or model["availability"] not in (
            "available", "unknown", "unavailable"):
        raise ValueError("availability: expected available, unknown or unavailable")


def _snapshot(value: Any, today: date) -> dict[Identity, dict[str, Any]]:
    snapshot = _object(value, {"reference", "date", "models"}, "harness")
    _text(snapshot["reference"], "harness.reference")
    if _date(snapshot["date"], today, "harness.date") != today:
        raise ValueError("harness.date: observe support for this invocation on the current date")
    if not isinstance(snapshot["models"], list):
        raise ValueError("harness.models: expected an array")
    result: dict[Identity, dict[str, Any]] = {}
    for raw in snapshot["models"]:
        model = _object(raw, {"provider", "id", "availability", "context_window", "tools"}, "harness model")
        key = _identity({name: model[name] for name in ("provider", "id")})
        if key in result:
            raise ValueError("harness.models: duplicate provider/id")
        _limits(model)
        result[key] = model
    return result


def _quality(model: dict[str, Any], today: date) -> int | None:
    evidence = model.get("capability_evidence")
    if evidence is None:
        return None
    try:
        evidence = _object(evidence, {"reference", "date", "quality"}, "capability_evidence")
        _text(evidence["reference"], "capability_evidence.reference")
        _date(evidence["date"], today, "capability_evidence.date")
        quality = evidence["quality"]
        if type(quality) is int and 1 <= quality <= 5:
            return quality
    except ValueError:
        pass
    return None


def _exclusions(model: dict[str, Any], actual: dict[str, Any] | None,
                context: SelectionContext) -> list[str]:
    reasons = []
    key = _identity({name: model[name] for name in ("provider", "id")})
    if model["availability"] != "available":
        reasons.append("catalog-unavailable")
    if actual is None or actual["availability"] != "available":
        reasons.append("harness-unavailable")
    for limits in (model, actual):
        if limits is None:
            continue
        if limits["context_window"] is None or limits["context_window"] < context.requirements["context_tokens"]:
            reasons.append("context-insufficient")
        if limits["tools"] is None or not set(context.requirements["tools"]) <= set(limits["tools"]):
            reasons.append("tools-unsupported")
    if (key in context.owner["excluded_models"] or (context.owner["allowed_models"] is not None
                                                    and key not in context.owner["allowed_models"])):
        reasons.append("owner-excluded")
    quality = _quality(model, context.today)
    if quality is None:
        reasons.append("quality-unknown")
    elif quality < context.floor:
        reasons.append("quality-below-floor")
    if not set(context.traits) <= set(model["traits"]):
        reasons.append("traits-unsupported")
    return list(dict.fromkeys(reasons))


def _total(value: Any) -> Decimal:
    if not isinstance(value, str) or not re.fullmatch(r"(?:0|[1-9]\d*)(?:\.\d+)?", value):
        raise ValueError("total cost: expected a nonnegative finite decimal string")
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("total cost: invalid decimal") from error
    if not result.is_finite():
        raise ValueError("total cost: expected a finite decimal")
    return result


def _comparison(raw: Any, context: SelectionContext) -> tuple[str, CostIntervals]:
    comparison = _object(raw, {"reference", "date", "qualification", "task_class", "quality_floor",
                               "traits", "requirements", "currency", "estimates"}, "cost comparison")
    _text(comparison["reference"], "cost comparison.reference")
    _date(comparison["date"], context.today, "cost comparison.date")
    _text(comparison["currency"], "cost comparison.currency")
    if (comparison["qualification"] != "comparable-task-evaluation"
            or comparison["task_class"] != context.request["task_class"]
            or type(comparison["quality_floor"]) is not int
            or not context.floor <= comparison["quality_floor"] <= 5
            or normalize_traits(comparison["traits"]) != context.traits):
        raise ValueError("cost comparison: workload/result-quality qualification does not cover this request")
    requirements = _requirements(comparison["requirements"])
    if (requirements["context_tokens"] < context.requirements["context_tokens"]
            or not set(context.requirements["tools"]) <= set(requirements["tools"])):
        raise ValueError("cost comparison: task requirements are not comparable")
    if not isinstance(comparison["estimates"], list) or not comparison["estimates"]:
        raise ValueError("cost comparison.estimates: expected a nonempty array")
    estimates = {}
    for raw_estimate in comparison["estimates"]:
        estimate = _object(raw_estimate, {"provider", "id", "total_cost_lower", "total_cost_upper"}, "cost estimate")
        key = _identity({name: estimate[name] for name in ("provider", "id")})
        lower, upper = _total(estimate["total_cost_lower"]), _total(estimate["total_cost_upper"])
        if key in estimates or lower > upper:
            raise ValueError("cost comparison: duplicate identity or reversed cost interval")
        estimates[key] = lower, upper
    return comparison["reference"], estimates


def _cost_proposal(eligible: dict[Identity, dict[str, Any]], baseline: Identity,
                   estimates: CostIntervals) -> Identity:
    # Only evidenced totals can win. Equal or overlapping intervals retain the baseline.
    comparable = [key for key in eligible if key in estimates]
    winners = [key for key in comparable if key != baseline and all(
        estimates[key][1] < estimates[other][0] for other in comparable if other != key)]
    return winners[0] if len(winners) == 1 else baseline


def _economics(eligible: dict[Identity, dict[str, Any]], baseline: Identity,
               context: SelectionContext) -> tuple[Identity, list[str], list[str]]:
    if not context.request["cost_comparisons"]:
        return baseline, [], ["No qualified comparable total-cost evidence; token prices and cost bands are insufficient."]
    proposals: list[Identity] = []
    references: list[str] = []
    uncertainty: list[str] = []
    for raw in context.request["cost_comparisons"]:
        try:
            reference, estimates = _comparison(raw, context)
        except (ValueError, TypeError) as error:
            uncertainty.append(f"Ignored unqualified economics: {error}")
            continue
        if baseline not in estimates:
            uncertainty.append(f"{reference}: default/strongest baseline total cost is unknown.")
            continue
        references.append(reference)
        proposals.append(_cost_proposal(eligible, baseline, estimates))
        if proposals[-1] == baseline:
            uncertainty.append(f"{reference}: equal, overlapping or incomplete totals retain the baseline.")
    if proposals and len(set(proposals)) == 1 and not uncertainty:
        return proposals[0], references, []
    if len(set(proposals)) > 1:
        uncertainty.append("Qualified comparisons disagree; retain the suitable baseline.")
    return baseline, references, uncertainty


def _context(request: dict[str, Any], today: date) -> SelectionContext:
    request = _object(request, REQUEST_KEYS, "selection request")
    floor = quality_floor(request["scores"], request["hard_constraints"])
    traits = normalize_traits(request["traits"])
    _text(request["task_class"], "task_class")
    requirements = _requirements(request["requirements"])
    snapshot = _snapshot(request["harness"], today)
    raw_owner = _object(request["owner"], {"allowed_models", "excluded_models"}, "owner")
    owner = {"allowed_models": None if raw_owner["allowed_models"] is None else _identity_list(raw_owner["allowed_models"]),
             "excluded_models": _identity_list(raw_owner["excluded_models"])}
    default = None if request["default_model"] is None else _identity(request["default_model"])
    if not isinstance(request["cost_comparisons"], list):
        raise ValueError("cost_comparisons: expected an array")
    return SelectionContext(request=request, floor=floor, traits=traits, requirements=requirements,
                            snapshot=snapshot, owner=owner, default=default, today=today)


def _eligible_models(catalog: dict[str, Any], context: SelectionContext
                     ) -> tuple[dict[Identity, dict[str, Any]], list[dict[str, Any]]]:
    if (not isinstance(catalog, dict) or type(catalog.get("schema_version")) is not int
            or catalog["schema_version"] != 1 or not isinstance(catalog.get("models"), list)):
        raise ValueError("catalog: expected a validated schema-version-1 payload")
    eligible: dict[Identity, dict[str, Any]] = {}
    excluded = []
    seen: set[Identity] = set()
    for model in catalog["models"]:
        if not isinstance(model, dict) or not {"provider", "id", "availability", "context_window", "tools", "traits"} <= set(model):
            raise ValueError("catalog: expected validated model fields")
        key = _identity({name: model[name] for name in ("provider", "id")})
        if key in seen:
            raise ValueError("catalog: duplicate provider/id")
        seen.add(key)
        _limits(model)
        if any(trait not in TRAITS for trait in _strings(model["traits"], "catalog model.traits")):
            raise ValueError("catalog model.traits: expected canonical traits")
        reasons = _exclusions(model, context.snapshot.get(key), context)
        if reasons:
            excluded.append({**_display(key), "reasons": reasons})
        else:
            eligible[key] = model
    return eligible, excluded


def _report(context: SelectionContext, eligible: dict[Identity, dict[str, Any]],
            excluded: list[dict[str, Any]]) -> dict[str, Any]:
    return {"status": "stopped", "selected": None, "quality_floor": context.floor,
            "traits": context.traits, "eligible": [_display(key) for key in sorted(eligible)],
            "excluded": sorted(excluded, key=lambda item: (item["provider"], item["id"])),
            "reasons": [], "evidence": [], "uncertainty": []}


def select_model(catalog: dict[str, Any], request: dict[str, Any], today: date) -> dict[str, Any]:
    """Recommend after all eligibility checks; malformed inputs raise ValueError.

    Request keys: scores, hard_constraints, traits, task_class, requirements, harness,
    owner, default_model, cost_comparisons. Identities always contain provider and id.
    requirements={context_tokens,tools}; harness={reference,date,models:[{provider,id,
    availability,context_window,tools}]}; owner={allowed_models:null|[identity],
    excluded_models:[identity]}; default_model=null|identity. Empty cost_comparisons
    retain a suitable default. No eligible model returns status=stopped, selected=null.
    """
    context = _context(request, today)
    eligible, excluded = _eligible_models(catalog, context)
    report = _report(context, eligible, excluded)
    if not eligible:
        report["reasons"] = ["No model satisfies availability, context, tools, owner, quality and trait constraints."]
        return report
    baseline = context.default if context.default in eligible else min(
        eligible, key=lambda key: (-eligible[key]["capability_evidence"]["quality"], key))
    selected, references, uncertainty = _economics(eligible, baseline, context)
    retained = "Retained suitable session default" if context.default == baseline else "Used strongest eligible baseline"
    report.update(status="selected", selected=_display(selected), uncertainty=uncertainty,
                  reasons=[f"{retained}; all eligibility constraints were checked before economics."
                           if selected == baseline else "Qualified comparable total-cost intervals justify this recommendation."],
                  evidence=[request["harness"]["reference"], eligible[selected]["capability_evidence"]["reference"], *references])
    return report
