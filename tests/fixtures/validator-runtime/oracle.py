"""Collect source contracts and validate controlled measurement manifests."""


import gzip
import re
import statistics
import hashlib
import json
import math
import ast
import sys

RESOURCE_PATTERNS = {
    "source_writes": r"write_text|write_bytes|open\(.+['\"][wax]|shutil\.(copy|move)|\b(cp|mv|touch|mkdir)\b",
    "bytecode": r"__pycache__|\.pyc|PYTHONDONTWRITEBYTECODE|PYTHONPYCACHEPREFIX",
    "fixed_paths": r"/tmp/|Path\([\"']/|(/dev/|/proc/|/var/)",
    "locks": r"\b(flock|lock|Lock|lockfile)\b",
    "ports": r"\b(socket|bind|listen|localhost|127\.0\.0\.1|port)\b",
    "inherited_stores": r"\b(HOME|XDG_[A-Z_]+|ORCHESTRAIL_[A-Z_]+|environ|os\.getenv)\b",
    "runtime_bounds": r"\b(timeout|deadline|sleep|join|monotonic|time\.time|SIGKILL|SIGTERM)\b",
}
ADDITIVE_RESULTS = [
    ("test_nested_validator_source_guard",
     "\"$(test_nested_validator_source_guard && echo pass || echo 'nested validator source inspection must pass')\""),
    ("test_validator_runtime_warning",
     "\"$(test_validator_runtime_warning && echo pass || echo 'warning fixture contracts must pass')\""),
    ("test_validator_runtime_characterization",
     "\"$(test_validator_runtime_characterization && echo pass || echo 'validator runtime characterization must pass')\""),
    ("test_validator_runtime_oracle",
     "\"$(test_validator_runtime_oracle && echo pass || echo 'validator runtime oracle must pass')\""),
]


# Preserve existing nested check syntax while rejecting any unreviewed change.
NONSTANDARD_CHECKS_SHA256 = "1ef044c0fd54cd3291111bbb47d33a1731187c3219194e07def9b7ee6820ce74"
RUNTIME_WRAPPER_SHA256 = {
    "test_nested_validator_source_guard": "d0be98efd1411c8cb9a17752259f6dda6a68671f1e4f9ae51f081e952cefba85",
    "test_validator_runtime_warning": "d1d3ea1e1d31b8d94f67e1254bda8cb20ce253fbff2bf614f0273240fbf6c419",
    "test_validator_runtime_characterization": "852f08dbf484d6aade369756e9114dd45828e43fd4ef5bbb2680bdbefcd2ec55",
    "test_validator_runtime_oracle": "ce4c2d70312455dfe685ed060b75a2f9f881f4fd097c67f3309f47893b4ae830",
}


def local_dependencies(root, references):
    """Find local static Python imports; dynamic loading remains unresolved."""
    pending = list(references)
    seen = set()
    dynamic = []
    while pending:
        ref = pending.pop()
        if ref in seen:
            continue
        seen.add(ref)
        path = root / ref
        if not path.is_file() or path.suffix != '.py':
            continue
        try:
            tree = ast.parse(path.read_bytes(), filename=ref)
        except (SyntaxError, UnicodeError, OSError):
            dynamic.append({"path": ref, "reason": "source could not be parsed"})
            continue
        literal_bindings = {}
        for statement in ast.walk(tree):
            if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
                values = [item.value for item in ast.walk(statement.value)
                          if isinstance(item, ast.Constant) and isinstance(item.value, str)]
                candidates = [value for value in values if value.startswith(('scripts/', 'tests/')) and (root / value).is_file()]
                for directory in ('scripts', 'tests'):
                    if directory in values:
                        candidates.extend(directory + '/' + value for value in values
                                          if value.endswith('.py') and (root / directory / value).is_file())
                if candidates:
                    literal_bindings.setdefault(statement.targets[0].id, set()).update(candidates)
        parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            elif isinstance(node, ast.Call):
                fn = node.func
                if ((isinstance(fn, ast.Name) and fn.id in {'__import__', 'exec', 'eval'}) or
                    (isinstance(fn, ast.Attribute) and fn.attr in {'import_module', 'spec_from_file_location', 'run_path'})):
                    literals = [item.value for item in ast.walk(node) if isinstance(item, ast.Constant) and isinstance(item.value, str)]
                    resolved = []
                    for item in ast.walk(node):
                        if isinstance(item, ast.Name) and item.id in literal_bindings:
                            resolved.extend(literal_bindings[item.id])
                        if (isinstance(item, ast.Call) and isinstance(item.func, ast.Attribute)
                                and item.func.attr == 'with_name' and len(item.args) == 1
                                and isinstance(item.args[0], ast.Constant) and isinstance(item.args[0].value, str)):
                            candidate = (path.parent / item.args[0].value).relative_to(root).as_posix()
                            if (root / candidate).is_file():
                                resolved.append(candidate)
                    for value in literals:
                        if value.startswith(('scripts/', 'tests/')) and (root / value).is_file():
                            resolved.append(value)
                        if value.endswith('.py') and (path.parent / value).is_file():
                            if any(isinstance(item, ast.Name) and item.id == '__file__' for item in ast.walk(node)):
                                resolved.append((path.parent / value).relative_to(root).as_posix())
                    for directory in ('scripts', 'tests'):
                        if directory in literals:
                            for value in literals:
                                candidate = directory + '/' + value
                                if value.endswith('.py') and (root / candidate).is_file():
                                    resolved.append(candidate)
                    if resolved:
                        pending.extend(resolved)
                        dynamic.append({"path": ref, "line": node.lineno, "reason": "literal dynamic target candidate",
                                        "target_candidates": sorted(set(resolved))})
                    else:
                        parent = parents.get(node)
                        while parent is not None and not isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            parent = parents.get(parent)
                        candidates = set()
                        if parent is not None:
                            function_literals = {item.value for item in ast.walk(parent)
                                                 if isinstance(item, ast.Constant) and isinstance(item.value, str)}
                            for call in ast.walk(tree):
                                if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == parent.name:
                                    for argument in ast.walk(call):
                                        if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                                            value = argument.value
                                            if value.startswith(('scripts/', 'tests/')) and (root / value).is_file():
                                                candidates.add(value)
                                            for directory in ('scripts', 'tests'):
                                                if directory in function_literals and (root / directory / value).is_file():
                                                    candidates.add(directory + '/' + value)
                                            sibling = path.parent / (value + '.py')
                                            if '.py' in function_literals and sibling.is_file():
                                                candidates.add(sibling.relative_to(root).as_posix())
                        pending.extend(candidates)
                        reason = "dynamic loading unresolved"
                        if isinstance(fn, ast.Name) and fn.id == '__import__' and node.args and isinstance(node.args[0], ast.Constant):
                            module = node.args[0].value
                            if isinstance(module, str) and module in sys.stdlib_module_names:
                                reason = "literal standard library import"
                            elif isinstance(module, str):
                                for directory in ('scripts', 'tests'):
                                    candidate = f'{directory}/{module}.py'
                                    if (root / candidate).is_file():
                                        pending.append(candidate)
                                        candidates.add(candidate)
                        dynamic.append({"path": ref, "line": node.lineno, "reason": reason,
                                        "callsite_candidates": sorted(candidates)})
            for name in names:
                module = name.split('.')[0]
                for directory in ('tests', 'scripts'):
                    candidate = f'{directory}/{module}.py'
                    if (root / candidate).is_file() and candidate not in seen:
                        pending.append(candidate)
    return sorted(seen), sorted(dynamic, key=lambda item: (item['path'], item.get('line', 0)))


def load_inventory(path):
    """Load the losslessly compressed frozen inventory."""
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def inventory(source, include_resources=True):
    text = source.read_text()
    nonstandard = [line for line in text.splitlines()
                   if re.search(r'\bcheck\b', line) and not line.startswith('check "')]
    # Reconstruct the sole removed loop check at its pinned position before
    # comparing with the original, unchanged nonstandard source fingerprint.
    removed = '  check "ORCH: no work-item id used as commit scope in $(basename $f)" \\'
    if removed in nonstandard or len(nonstandard) != 94:
        raise ValueError("Unapproved check syntax")
    restored = nonstandard[:20] + [removed] + nonstandard[20:]
    if hashlib.sha256("\n".join(restored).encode()).hexdigest() != NONSTANDARD_CHECKS_SHA256:
        raise ValueError("Unapproved check syntax")
    for name, digest in RUNTIME_WRAPPER_SHA256.items():
        escaped = re.escape(name)
        declarations = re.findall(r'^[ \t]*(?:function[ \t]+' + escaped + r'\b|' + escaped + r'[ \t]*\([ \t]*\))', text, re.M)
        wrappers = re.findall(r'^' + escaped + r'\(\) \{\n.*?^\}', text, re.M | re.S)
        if (len(declarations) != 1 or len(wrappers) != 1 or
                hashlib.sha256(wrappers[0].encode()).hexdigest() != digest):
            raise ValueError("Runtime wrapper differs")
    lines = text.splitlines(keepends=True)
    def marker(value):
        found = [index for index, line in enumerate(lines) if line.startswith(value)]
        if len(found) != 1:
            raise ValueError(f"Expected exactly one marker: {value}")
        return found[0]
    start = marker("# ── End public identity smoke checks")
    end = marker("hygiene_tracked_tree_result() {")
    region = "".join(lines[start + 1:end])
    check_pattern = r'^check "((?:\\.|[^"\\\n])+)"[ \t]+(?:\\\n[ \t]*)?([^\n]+)'
    checks = re.findall(check_pattern, region, re.M)
    expressions = []
    resources = []
    for name, expression in checks:
        called = re.search(r'\$\(([a-zA-Z_][a-zA-Z_0-9]*)', expression)
        body = ""
        if called:
            function = re.search(r'^' + re.escape(called.group(1)) + r'\(\) \{\n.*?^\}', text, re.M | re.S)
            if function:
                body = function.group(0)
        expressions.append({"name": name, "expression": expression, "body": body})
        if not include_resources:
            continue
        refs = sorted(set(re.findall(r'(?<![A-Za-z0-9_])(tests/[A-Za-z0-9_.-]+)', body + expression)))
        direct_refs = set(refs)
        refs, dynamic = local_dependencies(source.parent.parent, refs)
        references = []
        observations = {kind: [] for kind in RESOURCE_PATTERNS}
        for ref in refs:
            path = source.parent.parent / ref
            if not path.is_file():
                references.append({"path": ref, "status": "unresolved"})
                continue
            data = path.read_bytes()
            references.append({"path": ref, "sha256": hashlib.sha256(data).hexdigest(),
                               "provenance": "direct lexical reference" if ref in direct_refs
                               else "static import or dynamic target candidate"})
            for line_number, line in enumerate(data.decode("utf-8", "replace").splitlines(), 1):
                for kind, pattern in RESOURCE_PATTERNS.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        observations[kind].append({"path": ref, "line": line_number,
                                                   "line_sha256": hashlib.sha256(line.encode()).hexdigest()})
        resources.append({"name": name, "classification": "exclusive",
                          "evidence": "Lexical observations are not proof of isolation; serialize until each conflict and bound is audited.",
                          "source_references": references,
                          "dynamic_dependencies": dynamic,
                          "transitive_status": "unresolved", "observations": observations})
    focused = []
    for match in re.finditer(r'^if \[ "\$\{1:-\}" = (--[^ ]+) \]; then\n.*?^fi$', text, re.M | re.S):
        focused.append({"flag": match.group(1), "dispatch": match.group(0)})
    identity_start = 'check "test_validator_runtime_identity"'
    identity_end = "\n# ── End public identity smoke checks"
    if text.count(identity_start) != 1 or text.count(identity_end) != 1:
        raise ValueError("Identity registration is missing or duplicated")
    identity_block = text[text.index(identity_start):text.index(identity_end)]
    if hashlib.sha256(identity_block.encode()).hexdigest() != "c5b98d906511828e339f4619e99cb329d5a86063cb8e9a09f9e77fc93b7c7acb":
        raise ValueError("Identity registration differs")
    all_results = re.findall(check_pattern, text, re.M)
    identity_names = [name for name, _ in all_results]
    index = identity_names.index("test_validator_runtime_identity") if "test_validator_runtime_identity" in identity_names else -1
    if (index >= 1 and identity_names[index - 1] == "test_public_identity_matches_exact_ledger_and_preserves_knowledge"
            and index + 1 < len(identity_names) and identity_names[index + 1] == "test_usage_warning_acceptance"):
        del all_results[index]
    if (all_results[-len(ADDITIVE_RESULTS):] != ADDITIVE_RESULTS or
            any(name in {item[0] for item in ADDITIVE_RESULTS}
                for name, _ in all_results[:-len(ADDITIVE_RESULTS)])):
        raise ValueError("Runtime checks do not match the approved suffix")
    results = [{"name": name, "expression": expression} for name, expression in
               all_results[:-len(ADDITIVE_RESULTS)]]
    if len(expressions) != 36 or len(focused) != 37:
        raise ValueError("Source does not match the expected acceptance or focused inventory")
    return {"results": results, "expressions": expressions, "focused": focused, "resources": resources}


def matches_structure(expected, actual):
    """Compare every frozen source contract before expensive resource analysis."""
    return all(expected[key] == actual[key] for key in ("results", "expressions", "focused"))


def matches(expected, actual):
    return expected == actual


def extract_results(data, expected):
    summary = re.findall(rb'^=== Contract Validation ===\n  Passed: (\d+)\n  Failed: (\d+)\n  Skipped: (\d+)$', data, re.M)
    if len(summary) != 1:
        return None
    counts = tuple(map(int, summary[0]))
    try:
        entries = [(kind.decode(), name.decode('utf-8')) for kind, name in
                   re.findall(rb'^\[(PASS|FAIL|SKIP)\] ([^\n]*)$', data, re.M)]
    except UnicodeError:
        return None
    if expected is None:
        if counts[1] or len(entries) != sum(counts):
            return None
        if tuple(sum(status == kind for status, _ in entries) for kind in ('PASS', 'FAIL', 'SKIP')) != counts:
            return None
        return entries
    def match(entry, name):
        status, text = entry
        return text == name if status == 'PASS' else text.startswith(name + ': ')
    def select(names, candidates):
        selected = []
        iterator = iter(candidates)
        for name in names:
            for entry in iterator:
                if match(entry, name):
                    selected.append((entry[0], name))
                    break
            else:
                return None
        return selected
    forward = select(expected, entries)
    backward = select(reversed(expected), reversed(entries))
    if forward is None or backward is None or forward != list(reversed(backward)):
        return None
    if tuple(sum(status == kind for status, _ in forward) for kind in ('PASS', 'FAIL', 'SKIP')) != counts:
        return None
    return forward


def verify_provenance(record, root, trusted):
    fields = ("commit", "source_blob", "source_files", "configuration", "result_inventory")
    if not isinstance(record, dict) or not isinstance(trusted, dict) or set(trusted) != set(fields):
        return False
    if any(key not in record or record[key] != trusted[key] for key in fields):
        return False
    if any(not isinstance(trusted[key], str) or not re.fullmatch(r'[0-9a-f]{40}', trusted[key])
           for key in ("commit", "source_blob")):
        return False
    return verify_evidence(record, root)


def parse_time(data):
    try:
        text = data.decode("utf-8")
        patterns = {"user_seconds": r"User time \(seconds\):\s*([0-9.]+)",
                    "system_seconds": r"System time \(seconds\):\s*([0-9.]+)",
                    "elapsed_seconds": r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s*([0-9:.]+)",
                    "max_rss_kb": r"Maximum resident set size \(kbytes\):\s*(\d+)",
                    "exit_code": r"Exit status:\s*(\d+)"}
        values = {}
        for name, pattern in patterns.items():
            found = re.findall(pattern, text)
            if len(found) != 1:
                return None
            if name == "elapsed_seconds":
                parts = found[0].split(":")
                if len(parts) not in (2, 3):
                    return None
                seconds = 0.0
                for part in parts:
                    seconds = seconds * 60 + float(part)
                values[name] = seconds
            elif name in ("max_rss_kb", "exit_code"):
                values[name] = int(found[0])
            else:
                values[name] = float(found[0])
        return values
    except (UnicodeError, ValueError, OverflowError):
        return None


def verify_evidence(record, root):
    if not isinstance(record, dict) or not valid_manifest(record, record.get("payload_sha256"),
                                                          record.get("configuration_sha256")):
        return False
    root = root.resolve()
    def read_file(name):
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("Evidence path is unavailable or outside its root")
        return path.read_bytes()
    try:
        configuration = record["configuration"]
        config_digest = hashlib.sha256(json.dumps(configuration, sort_keys=True, separators=(",", ":"),
                                                   allow_nan=False).encode()).hexdigest()
        if config_digest != record["configuration_sha256"]:
            return False
        source_files = record["source_files"]
        if not isinstance(source_files, dict) or not source_files:
            return False
        digest = hashlib.sha256()
        for path, expected in sorted(source_files.items()):
            data = read_file(path)
            if hashlib.sha256(data).hexdigest() != expected:
                return False
            digest.update(data)
        if digest.hexdigest() != record["payload_sha256"]:
            return False
        for sample in record["samples"]:
            if sample["process_exit_code"] != 0 or sample["source_files_unchanged"] is not True or sample["dirty_after"] != "":
                return False
            if sample["payload_sha256"] != record["payload_sha256"] or sample["configuration_sha256"] != record["configuration_sha256"]:
                return False
            data = {name: read_file(sample[name]) for name in ("stdout", "stderr", "time_output")}
            if any(hashlib.sha256(value).hexdigest() != sample["file_sha256"][name] for name, value in data.items()):
                return False
            timing = parse_time(data["time_output"])
            if timing is None or any(sample[field] != value for field, value in timing.items()):
                return False
            entries = extract_results(data["stdout"], None)
            if entries is None:
                return False
            names = [name for _, name in entries]
            if names != record["result_inventory"]:
                return False
            if tuple(sum(kind == status for kind, _ in entries) for status in ("PASS", "FAIL", "SKIP")) != (sample["pass_count"], sample["failures"], sample["skip_count"]):
                return False
            summary = re.findall(rb'^=== Contract Validation ===\n  Passed: (\d+)\n  Failed: (\d+)\n  Skipped: (\d+)$', data["stdout"], re.M)
            if len(summary) != 1 or tuple(map(int, summary[0])) != (sample["pass_count"], sample["failures"], sample["skip_count"]):
                return False
        return record["baseline_median_seconds"] == statistics.median(sample["elapsed_seconds"] for sample in record["samples"])
    except (KeyError, TypeError, ValueError, OSError, UnicodeError):
        return False


def valid_manifest(record, payload_sha256, configuration_sha256):
    required = ("commit", "source_blob", "payload_sha256", "configuration_sha256", "dirty_paths",
                "machine", "cpu_quota", "ram_bytes", "python_version", "bash_version", "grep_version",
                "locale", "cache_policy", "bytecode_existed", "hygiene_policy", "cpu_count", "jobs", "samples")
    sample_fields = ("exit_code", "failures", "elapsed_seconds", "user_seconds", "system_seconds",
                     "max_rss_kb", "pass_count", "skip_count", "stdout", "stderr", "time_output")
    if not isinstance(record, dict) or not all(key in record for key in required):
        return False
    if any(not isinstance(record[key], str) or not record[key] for key in
           ("commit", "source_blob", "payload_sha256", "configuration_sha256", "machine", "cpu_quota",
            "python_version", "bash_version", "grep_version", "locale", "cache_policy", "hygiene_policy")):
        return False
    if not isinstance(record["dirty_paths"], list) or not isinstance(record["bytecode_existed"], bool):
        return False
    if any(not isinstance(record[key], int) or isinstance(record[key], bool) or record[key] <= 0
           for key in ("ram_bytes", "cpu_count", "jobs")):
        return False
    if record["payload_sha256"] != payload_sha256 or record["configuration_sha256"] != configuration_sha256:
        return False
    samples = record["samples"]
    if not isinstance(samples, list) or len(samples) < 2:
        return False
    for item in samples:
        if not isinstance(item, dict) or not all(field in item for field in sample_fields):
            return False
        if item["exit_code"] != 0 or item["failures"] != 0:
            return False
        if any(not isinstance(item[field], str) or not item[field] for field in ("stdout", "stderr", "time_output")):
            return False
        if any(not isinstance(item[field], (float, int)) or isinstance(item[field], bool) or not math.isfinite(item[field]) or item[field] < 0
               for field in ("elapsed_seconds", "user_seconds", "system_seconds", "max_rss_kb", "pass_count", "skip_count")):
            return False
    if len({(item["pass_count"], item["failures"], item["skip_count"]) for item in samples}) != 1:
        return False
    values = [item["elapsed_seconds"] for item in samples]
    median = statistics.median(values)
    if median <= 0 or (len(samples) == 2 and max(values) - min(values) > median * 0.1):
        return False
    return True
