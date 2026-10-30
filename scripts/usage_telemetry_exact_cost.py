"""Exact arithmetic for already validated, independently priced components.

The caller must verify provenance, scope, identity, applicability, and coverage.
The coverage flags convey those conclusions; this module does not establish them.
"""

from fractions import Fraction
import re


_DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")
_COMPONENT_ID = re.compile(r"[A-Za-z0-9_.-]+\Z")
_REQUIRED_COMPLETE = (
    "inventory_complete", "identities_resolved", "quantities_final",
    "prices_applicable", "scope_proven", "nonoverlapping",
)
_RESTRICT_LOWER_BOUND = (
    "contradiction", "historical_substitution", "unknown_signed_components",
)


def _is_terminating(value):
    denominator = value.denominator
    for factor in (2, 5):
        while denominator % factor == 0:
            denominator //= factor
    return denominator == 1


def _parse_digits(digits):
    result = 0
    for start in range(0, len(digits), 9):
        chunk = digits[start:start + 9]
        result = result * 10 ** len(chunk) + int(chunk)
    return result


def _format_integer(value):
    if value == 0:
        return "0"
    chunks = []
    while value:
        value, chunk = divmod(value, 1_000_000_000)
        chunks.append(chunk)
    return str(chunks[-1]) + "".join(f"{chunk:09d}" for chunk in reversed(chunks[:-1]))


def _decimal_string(value):
    """Return an exact, normalized finite decimal without a precision context."""
    denominator = value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        raise ValueError("value is not a finite decimal")
    scale = max(twos, fives)
    scaled = value.numerator * 2 ** (scale - twos) * 5 ** (scale - fives)
    digits = _format_integer(scaled).zfill(scale + 1)
    if not scale:
        return digits
    text = digits[:-scale] + "." + digits[-scale:]
    return text.rstrip("0").rstrip(".")


def _display(value):
    cents, remainder = divmod(value.numerator * 100, value.denominator)
    doubled = remainder * 2
    if doubled > value.denominator or (doubled == value.denominator and cents % 2):
        cents += 1
    return f"{_format_integer(cents // 100)}.{cents % 100:02d}"


def _integer(value, name, *, positive=False):
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    if value < (1 if positive else 0):
        raise ValueError(f"invalid {name}")
    return value


def _rate(price, unit):
    if not isinstance(price, str):
        raise TypeError("price must be a decimal string")
    if not _DECIMAL.fullmatch(price):
        raise ValueError("invalid decimal price")
    unit = _integer(unit, "unit", positive=True)
    whole, _, fractional = price.partition(".")
    return Fraction(_parse_digits(whole + fractional), 10 ** len(fractional) * unit)


def calculate_cost(components, coverage):
    """Compute a scoped cost from components and verified upstream conclusions.

    IDs must uniquely identify non-overlapping components. An unpriced component
    uses null price and unit. A repeating unit rate is unpriced even if a specific
    quantity would cancel its denominator. No currency conversion is performed.
    """
    flags = _REQUIRED_COMPLETE + _RESTRICT_LOWER_BOUND + ("excluded_cannot_reduce",)
    if not isinstance(coverage, dict) or any(type(coverage.get(key)) is not bool for key in flags):
        raise ValueError("all coverage conclusions must be explicit booleans")
    total = Fraction(0)
    seen = set()
    unpriced = []
    unpriced_reasons = {}
    for item in components:
        if not isinstance(item, dict):
            raise TypeError("component must be an object")
        name = item.get("id")
        if not isinstance(name, str) or not _COMPONENT_ID.fullmatch(name):
            raise ValueError("invalid component ID")
        if name in seen:
            raise ValueError("duplicate component ID")
        seen.add(name)
        quantity = _integer(item.get("quantity"), "quantity")
        price = item.get("price_usd")
        unit = item.get("unit")
        if price is None and unit is None:
            unpriced.append(name)
            unpriced_reasons[name] = "missing_price"
            continue
        if price is None or unit is None:
            raise ValueError("price and unit must both be present or absent")
        rate = _rate(price, unit)
        if not _is_terminating(rate):
            unpriced.append(name)
            unpriced_reasons[name] = "unsupported_exact_unit"
            continue
        total += quantity * rate

    complete = (all(coverage[key] for key in _REQUIRED_COMPLETE)
                and not any(coverage[key] for key in _RESTRICT_LOWER_BOUND)
                and coverage["excluded_cannot_reduce"] and not unpriced)
    result = {"unpriced_ids": sorted(unpriced), "unpriced_reasons": dict(sorted(unpriced_reasons.items()))}
    if complete:
        result["cost_usd"] = _decimal_string(total)
        result["display_usd"] = _display(total)
    else:
        result["priced_subtotal_usd"] = _decimal_string(total)
        lower_bound = (coverage["nonoverlapping"] and coverage["scope_proven"]
                       and coverage["identities_resolved"] and coverage["quantities_final"]
                       and coverage["excluded_cannot_reduce"]
                       and not any(coverage[key] for key in _RESTRICT_LOWER_BOUND))
        result["subtotal_quality"] = "proven_lower_bound" if lower_bound else "subtotal_only"
    return result
