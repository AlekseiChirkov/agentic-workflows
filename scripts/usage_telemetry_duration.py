"""Compute offline timing measures from explicit interval evidence.

The caller is responsible for proving the declared graph is complete and for
supplying clock offsets that transform other clocks into the parent clock.
Milliseconds are integers; approximate and invalid intervals are never exact.
"""


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _bounds(item, parent_clock, offsets):
    if not isinstance(item, dict) or item.get("approximate", False) is not False:
        return None
    start, end, clock = item.get("start_ms"), item.get("end_ms"), item.get("clock")
    if not _integer(start) or not _integer(end) or end < start:
        return None
    if not isinstance(clock, str) or not clock:
        return None
    if clock == parent_clock:
        offset = 0
    else:
        offset = offsets.get(clock)
        if not _integer(offset):
            return None
    return start + offset, end + offset


def analyze_intervals(parent, children, *, complete=False, clock_offsets=None):
    """Return exact values where evidence supports them and observed coverage otherwise.

    ``coverage_ms`` is the union of valid direct children clipped to the parent
    window. ``coverage_complete`` distinguishes a partial observation from a
    complete consistent graph. Parentage must be explicit; descendants are
    checked but only direct children contribute to worker sum and coverage.
    """
    result = {"wall_ms": None, "worker_sum_ms": None, "coverage_ms": None,
              "exclusive_ms": None, "coverage_complete": False, "diagnostics": []}
    issues = result["diagnostics"]
    if not isinstance(parent, dict) or not isinstance(children, (list, tuple)):
        issues.append("invalid_input")
        return result
    parent_id, parent_clock = parent.get("id"), parent.get("clock")
    if not isinstance(parent_id, str) or not parent_id or not isinstance(parent_clock, str) or not parent_clock:
        issues.append("invalid_parent")
        return result
    if clock_offsets is None:
        clock_offsets = {}
    if not isinstance(clock_offsets, dict):
        issues.append("invalid_clock_offsets")
        return result
    parent_bounds = _bounds(parent, parent_clock, clock_offsets)
    if parent_bounds is None:
        issues.append("invalid_parent_interval")
        return result
    begin, end = parent_bounds
    result["wall_ms"] = end - begin
    graph = {parent_id: parent}
    ambiguous = False
    consistent = complete is True
    if not consistent:
        issues.append("incomplete_graph")
    for child in children:
        if not isinstance(child, dict) or not isinstance(child.get("id"), str) or not child["id"]:
            consistent = False
            ambiguous = True
            issues.append("invalid_interval")
            continue
        ident = child["id"]
        if ident in graph:
            if graph[ident] != child:
                consistent = False
                ambiguous = True
                issues.append("conflicting_identity")
            continue
        graph[ident] = child

    intervals = []
    worker_sum = 0
    worker_sum_known = True
    for ident, child in graph.items():
        if ident == parent_id:
            continue
        ancestor = child.get("parent_id")
        seen = {ident}
        while ancestor != parent_id:
            if not isinstance(ancestor, str) or ancestor not in graph or ancestor in seen:
                consistent = False
                ambiguous = True
                issues.append("invalid_parentage")
                break
            seen.add(ancestor)
            ancestor = graph[ancestor].get("parent_id")
        bounds = _bounds(child, parent_clock, clock_offsets)
        if bounds is None:
            consistent = False
            issues.append("invalid_or_incompatible_interval")
            if child.get("parent_id") == parent_id:
                worker_sum_known = False
            continue
        direct_parent_id = child.get("parent_id")
        immediate_parent = graph.get(direct_parent_id) if isinstance(direct_parent_id, str) else None
        outer = _bounds(immediate_parent, parent_clock, clock_offsets)
        if outer is None or bounds[0] < outer[0] or bounds[1] > outer[1]:
            consistent = False
            issues.append("outside_parent_interval")
        if child.get("parent_id") == parent_id:
            worker_sum += bounds[1] - bounds[0]
            clipped_start, clipped_end = max(begin, bounds[0]), min(end, bounds[1])
            if clipped_start < clipped_end:
                intervals.append((clipped_start, clipped_end))

    coverage = 0
    merged_end = None
    for start, finish in sorted(intervals):
        if merged_end is None or start > merged_end:
            coverage += finish - start
            merged_end = finish
        elif finish > merged_end:
            coverage += finish - merged_end
            merged_end = finish
    result["worker_sum_ms"] = worker_sum if worker_sum_known and not ambiguous else None
    result["coverage_ms"] = coverage if not ambiguous else None
    result["coverage_complete"] = consistent
    if consistent:
        result["exclusive_ms"] = result["wall_ms"] - coverage
    issues.sort()
    return result
