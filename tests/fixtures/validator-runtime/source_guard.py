"""Bounded source inspection for nested full-validator calls.

This scanner classifies known shell and Python forms; unknown executable forms fail
closed. It does not execute inspected source or claim to parse arbitrary shell.
"""
import argparse
import ast
import hashlib
import json
import re
import shlex
import sys
from pathlib import Path

FOCUSED_FLAGS = frozenset(["--usage-warning-only","--usage-report-only","--usage-resolution-only","--usage-publication-only","--usage-source-normalization-only","--usage-bounded-source-reads-only","--usage-contract-export-only","--usage-current-snapshot-only","--usage-projection-only","--usage-receipt-only","--usage-analysis-corpus-only","--usage-warning-policy-only","--usage-pricing-scenario-only","--usage-price-snapshot-only","--usage-diagnostic-registry-only","--usage-diagnostic-only","--usage-segment-only","--usage-attribution-only","--usage-inventory-only","--usage-selection-only","--usage-source-profiles-only","--usage-entity-only","--usage-envelope-only","--usage-schema-only","--usage-canonical-only","--model-workflow-only","--model-plan-only","--model-selection-only","--model-catalog-only","--hook-shell-quality-only","--hook-timing-only","--hook-workflow-only","--hook-install-only","--hook-adapter-only","--git-rails-only","--hygiene-only","--run-log-contract-only"])
WARNING_SHA256 = "a74f6c9e18840213d04ffb45f95ac6cb1752722c46348c6146a6cc7175ed0586"
WARNING_NAME = "test_contract_version_rule_history_warns_until_version_changes"
VALIDATOR = "validate-contracts.sh"


def _digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _exception(path, source, statement, exceptions, used):
    matching = [index for index, item in enumerate(exceptions)
                if isinstance(item, dict) and item.get("path") == path
                and item.get("statement") == statement
                and item.get("count") == 1 and item.get("reason")
                and item.get("context_sha256") == _digest(source)]
    if len(matching) != 1 or source.count(statement) != 1 or matching[0] in used:
        return False
    used.add(matching[0])
    return True


def _shell(path, source, exceptions, used):
    issues = []
    lines = source.splitlines()
    aliases = set()
    logical = []
    pending = ""
    start = 1
    for number, line in enumerate(lines, 1):
        if not pending:
            start = number
        pending += line.rstrip("\\")
        if line.endswith("\\"):
            pending += " "
            continue
        logical.append((start, pending))
        pending = ""
    if pending:
        issues.append(f"{path}:{start}: incomplete statement")
    for number, line in logical:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        assignment = re.match(r"^[ \t]*([A-Za-z_][A-Za-z_0-9]*)=", line)
        if assignment and "validate-" in line:
            try:
                assignment_words = shlex.split(line, comments=True)
            except ValueError:
                assignment_words = []
            if not assignment_words or any(VALIDATOR in value or "validate-contracts." in value for value in assignment_words):
                aliases.add(assignment.group(1))
                issues.append(f"{path}:{number}: validator alias requires review")
                continue
        alias_reference = any(re.search(r"\$\{?" + re.escape(name) + r"(?:\}|\b)", line) for name in aliases | {"validator"})
        static_reference = False
        if VALIDATOR not in line and "val" in line and "idate" in line:
            try:
                static_reference = any(VALIDATOR in word for word in shlex.split(line, comments=True))
            except ValueError:
                issues.append(f"{path}:{number}: unclassified shell reference")
                continue
        if VALIDATOR not in line and "validate-contracts." not in line and not alias_reference and not static_reference:
            dynamic_command = (
                re.search(r"\$\(\s*[\"']?\$(?:\{[A-Za-z_][A-Za-z_0-9]*\}|[A-Za-z_][A-Za-z_0-9]*)", line)
                or re.search(r"(?:^\s*|[;&|]\s*|\b(?:if|then|do|elif|while|until)\s+)[\"']?\$(?:\{[A-Za-z_][A-Za-z_0-9]*\}|[A-Za-z_][A-Za-z_0-9]*)", re.sub(r"\[\[.*?\]\]", "", line))
            )
            dynamic_executable = re.search(
                r"(?:^|[;&|()\s])(?:bash|sh|exec)\s+(?:(?:--?[A-Za-z0-9-]+)\s+)*[\"']?\$", line)
            if dynamic_command:
                issues.append(f"{path}:{number}: dynamic command requires review")
            elif dynamic_executable:
                issues.append(f"{path}:{number}: dynamic executable requires review")
            continue
        direct_substitution = any(
            re.search(r'''\$\(\s*["']?\$\{?''' + re.escape(name) + r'''(?:\}|\b)''', line)
            for name in aliases | {"validator"}
        )
        if assignment and direct_substitution:
            issues.append(f"{path}:{number}: validator alias substitution requires review")
            continue
        if re.match(r'^[A-Za-z_][A-Za-z_0-9]*=', stripped) and not re.search(r'\b(?:ba)?sh\b', stripped):
            continue
        if re.search(r'\bprintf\b', line) and re.search(r'>\s*[^\n]*validate-contracts\.sh', line):
            statement = stripped
            if not _exception(path, source, statement, exceptions, used):
                issues.append(f"{path}:{number}: unapproved generated validator")
            continue
        if re.search(r'(?:validate-contracts\.sh|\$\{?validator\}?)[^\n]*(?:\$\(|`|<\(|>\()', line):
            issues.append(f"{path}:{number}: dynamic validator argument requires review")
            continue
        try:
            lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|()<>")
            lexer.whitespace_split = True
            tokens = list(lexer)
        except ValueError:
            issues.append(f"{path}:{number}: unclassified shell reference")
            continue
        command = []
        commands = []
        for token in tokens + [";"]:
            if token in (";", "&&", "||", "|", "&"):
                if command:
                    commands.append(command)
                command = []
            else:
                command.append(token)
        found = False
        for argv in commands:
            targets = [index for index, value in enumerate(argv)
                       if VALIDATOR in value or any(re.search(r"\$\{?" + re.escape(name) + r"(?:\}|\b)", value) for name in aliases | {"validator"})]
            if not targets:
                continue
            found = True
            index = targets[0]
            prefix = argv[:index]
            executable = (index == 0 or any(value in ("bash", "sh", "exec") for value in prefix))
            if not executable:
                issues.append(f"{path}:{number}: unclassified shell reference")
            elif "-c" in prefix:
                issues.append(f"{path}:{number}: nested shell command requires review")
            elif index + 1 >= len(argv) or argv[index + 1] not in FOCUSED_FLAGS:
                issues.append(f"{path}:{number}: unapproved full validator")
        if not found:
            issues.append(f"{path}:{number}: unclassified shell reference")
    return issues


def _literal_string(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _literal_string(node.left), _literal_string(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _python(path, source):
    issues = []
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError:
        return [f"{path}: invalid Python source"]
    imported_calls = {alias.asname or alias.name
                      for node in ast.walk(tree)
                      if isinstance(node, ast.ImportFrom) and node.module == "subprocess"
                      for alias in node.names
                      if alias.name in {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"}}
    callable_aliases = set(imported_calls)
    aliases = set()
    changed = True
    while changed:
        changed = False
        for assignment in ast.walk(tree):
            if not isinstance(assignment, (ast.Assign, ast.AnnAssign)):
                continue
            targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
            value = assignment.value
            if value is None:
                continue
            relevant = any((_literal_string(item) is not None and "validate-contracts." in _literal_string(item)) or (isinstance(item, ast.Name) and item.id in aliases) for item in ast.walk(value))
            callable_value = ((isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name)
                               and value.value.id == "subprocess" and value.attr in {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"})
                              or (isinstance(value, ast.Name) and value.id in callable_aliases))
            for target in targets:
                if relevant and isinstance(target, ast.Name) and target.id not in aliases:
                    aliases.add(target.id)
                    changed = True
                if callable_value and isinstance(target, ast.Name) and target.id not in callable_aliases:
                    callable_aliases.add(target.id)
                    changed = True
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = fn.attr if isinstance(fn, ast.Attribute) else fn.id if isinstance(fn, ast.Name) else ""
        indirect = (isinstance(fn, ast.Call) and isinstance(fn.func, ast.Name) and fn.func.id == "getattr"
                    and fn.args and isinstance(fn.args[0], ast.Name) and fn.args[0].id == "subprocess")
        if indirect:
            name = "indirect_subprocess"
        known_call = name in {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput", "system", "exec", "indirect_subprocess"} | callable_aliases
        if not known_call:
            arguments = list(node.args) + [keyword.value for keyword in node.keywords]
            if any(_literal_string(item) is not None and VALIDATOR in _literal_string(item)
                   for argument in arguments for item in ast.walk(argument)):
                issue = f"{path}:{node.lineno}: unclassified Python reference"
                if issue not in issues:
                    issues.append(issue)
            continue
        keyword_args = [keyword.value for keyword in node.keywords if keyword.arg == "args"]
        commands = ([node.args[0]] if node.args else []) + keyword_args
        references = [item for command in commands for item in ast.walk(command) if
                      (_literal_string(item) is not None and VALIDATOR in _literal_string(item))
                      or (isinstance(item, ast.Name) and item.id in aliases | {"validator"})]
        if not references:
            continue
        if len(commands) != 1:
            issues.append(f"{path}:{node.lineno}: ambiguous Python invocation")
            continue
        arg = commands[0]
        if indirect:
            issues.append(f"{path}:{node.lineno}: unclassified indirect subprocess invocation")
            continue
        if any(keyword.arg in ("executable", None) for keyword in node.keywords):
            issues.append(f"{path}:{node.lineno}: subprocess executable override requires review")
            continue
        if any(keyword.arg == "shell" and not (isinstance(keyword.value, ast.Constant)
                                                  and keyword.value.value is False)
               for keyword in node.keywords):
            issues.append(f"{path}:{node.lineno}: subprocess shell mode requires review")
            continue
        if not isinstance(arg, (ast.List, ast.Tuple)):
            issues.append(f"{path}:{node.lineno}: unclassified Python invocation")
            continue
        values = [_literal_string(item) for item in arg.elts]
        target = next((index for index, value in enumerate(values)
                       if value is not None and VALIDATOR in value), None)
        if target is not None and "-c" in values[:target]:
            issues.append(f"{path}:{node.lineno}: nested shell command requires review")
        elif target is None or target + 1 >= len(values) or values[target + 1] not in FOCUSED_FLAGS:
            issues.append(f"{path}:{node.lineno}: unapproved full or dynamic validator")
    return issues


def inspect_sources(sources, exceptions=()):
    """Return nonempty diagnostics for unapproved nested-validator references."""
    issues = []
    used = set()
    for path, source in sources.items():
        if not isinstance(path, str) or not isinstance(source, str):
            issues.append("invalid source input")
            continue
        # Only the exact audited warning function can authorize these full calls.
        marker = WARNING_NAME + "() ("
        if marker in source:
            start = source.index(marker)
            end = source.find("\n)\n", start)
            if end >= 0:
                end += 3
                block = source[start:end]
                count = block.count('output="$(bash scripts/validate-contracts.sh 2>&1)"')
                if (path == "scripts/validate-contracts.sh" and source.count(marker) == 1
                        and _digest(block) == WARNING_SHA256 and count == 3):
                    source = source[:start] + "\n" * block.count("\n") + source[end:]
                elif count:
                    issues.extend(f"{path}: warning invocation {index + 1} is unapproved"
                                  for index in range(count))
                    source = source[:start] + "\n" * block.count("\n") + source[end:]
        issues.extend(_python(path, source) if path.endswith(".py") else
                      _shell(path, source, exceptions, used))
    for index in range(len(exceptions)):
        if index not in used:
            issues.append("stale or duplicate exception")
    return issues


def inventory_sources(root):
    """Read the validator and regular test shell/Python sources without executing them."""
    root = Path(root).resolve()
    paths = [root / "scripts/validate-contracts.sh"]
    tests = root / "tests"
    if not tests.is_dir() or not paths[0].is_file():
        raise ValueError("validator source or tests directory is missing")
    paths.extend(path for path in tests.rglob("*") if path.suffix in (".sh", ".py") and path.is_file())
    result = {}
    for path in sorted(paths):
        if not path.resolve().is_relative_to(root):
            raise ValueError("source points outside the project")
        result[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8")
    return result



def _context(path, source, number):
    lines = source.splitlines()
    if number < 1 or number > len(lines):
        raise ValueError("diagnostic line is outside the source")
    if path.endswith(".py"):
        tree = ast.parse(source, filename=path)
        functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                     and node.lineno <= number <= node.end_lineno]
        if functions:
            node = min(functions, key=lambda item: item.end_lineno - item.lineno)
            return node.name, "\n".join(lines[node.lineno - 1:node.end_lineno])
    else:
        starts = []
        for index, line in enumerate(lines):
            match = re.match(r'^([A-Za-z_][A-Za-z_0-9]*)\(\)\s*[{(]', line)
            if match:
                starts.append((index, match.group(1), "}" if "{" in line else ")"))
        for start, name, terminator in reversed(starts):
            if start >= number:
                continue
            end = next((index for index in range(start + 1, len(lines))
                        if lines[index] == terminator), None)
            if end is not None and start <= number - 1 <= end:
                return name, "\n".join(lines[start:end + 1])
        for index in range(number - 1, -1, -1):
            match = re.search(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z_0-9]*)['\"]?", lines[index])
            if not match:
                continue
            label = match.group(1)
            end = next((i for i in range(index + 1, len(lines)) if lines[i] == label), None)
            if end is not None and index <= number - 1 <= end:
                return "heredoc:" + label, "\n".join(lines[index:end + 1])
    end = number
    while end < len(lines) and lines[end - 1].endswith("\\"):
        end += 1
    return "top-level", "\n".join(lines[number - 1:end])


def inspect_project(root, classified=()):
    """Inspect all regular project sources with exact classified-reference records."""
    sources = inventory_sources(root)
    issues = inspect_sources(sources)
    consumed = {}
    remaining = []
    for issue in issues:
        match = re.fullmatch(r"(.+?):([0-9]+): (.+)", issue)
        if not match:
            remaining.append(issue)
            continue
        path, number, detail = match.group(1), int(match.group(2)), match.group(3)
        source = sources.get(path)
        if source is None:
            remaining.append(issue)
            continue
        try:
            container, context = _context(path, source, number)
            statement = source.splitlines()[number - 1]
        except (ValueError, IndexError, SyntaxError):
            remaining.append(issue)
            continue
        def dependencies_match(entry):
            dependencies = entry.get("dependencies", {})
            if not isinstance(dependencies, dict):
                return False
            base = Path(root).resolve()
            try:
                for name, expected in dependencies.items():
                    target = (base / name).resolve()
                    if not target.is_relative_to(base) or not target.is_file():
                        return False
                    if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
                        return False
            except (OSError, TypeError, ValueError):
                return False
            return True
        candidates = [index for index, entry in enumerate(classified)
                      if isinstance(entry, dict) and entry.get("path") == path
                      and entry.get("statement") == statement and entry.get("container") == container
                      and entry.get("context_sha256") == _digest(context)
                      and entry.get("detail") == detail and isinstance(entry.get("count"), int)
                      and entry.get("count") > 0 and entry.get("count") == context.splitlines().count(statement)
                      and isinstance(entry.get("reason"), str) and entry.get("reason").strip()
                      and dependencies_match(entry)]
        if len(candidates) == 1 and consumed.get(candidates[0], 0) < classified[candidates[0]]["count"]:
            consumed[candidates[0]] = consumed.get(candidates[0], 0) + 1
        else:
            remaining.append(issue)
    remaining.extend("stale or duplicate classified reference" for index, entry in enumerate(classified)
                     if not isinstance(entry, dict) or consumed.get(index, 0) != entry.get("count"))
    return remaining



def main(argv=None):
    parser = argparse.ArgumentParser(description="Check bounded nested-validator source references.")
    parser.add_argument("--root", required=True, help="Project source root")
    args = parser.parse_args(argv)
    manifest = Path(__file__).with_name("source_guard_exceptions.json")
    try:
        data = manifest.read_bytes()
        if hashlib.sha256(data).hexdigest() != "cc1a2a828c365709a4c051509af61e06a68ba4d62a560085c577dfa8135628d5":
            raise ValueError("classified reference manifest digest differs")
        exceptions = json.loads(data)
        if not isinstance(exceptions, list):
            raise ValueError("classified reference manifest must be a list")
        source = (Path(args.root) / "scripts/validate-contracts.sh").read_text(encoding="utf-8")
        flags = set(re.findall(r'^if \[ "\$\{1:-\}" = (--[^ ]+) \]; then$', source, re.M))
        if flags != FOCUSED_FLAGS:
            raise ValueError("focused dispatch inventory differs")
        issues = inspect_project(args.root, exceptions)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        print(f"nested validator source guard: {error}", file=sys.stderr)
        return 2
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        return 1
    print("nested validator source guard: pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
