"""Bounded source inspection for nested full-validator calls.

This scanner classifies bounded shell and Python forms and rejects detected unknown
executables. Dynamic reflection and arbitrary shell are not comprehensively parsed.
It does not execute inspected source.
"""
import argparse
import ast
from functools import lru_cache
import hashlib
import json
import re
import shlex
import symtable
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


def _direct_path_command(line):
    """Identify path-named commands at shell command boundaries."""
    if re.search('(?:^|[;&|])\\s*(?:\\(\\s*|\\{\\s+)(?:[A-Za-z_][A-Za-z_0-9]*=(?:[^\\s;|&()\'\\"]|\'[^\']*\'|\\"[^\\"]*\\")*\\s+)*(?:exec\\s+)?[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+(?:\\s|[;)]|$)', line):
        return True
    try:
        lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|()")
        lexer.whitespace_split = True
        lexer.commenters = "#"
        tokens = list(lexer)
    except ValueError:
        return False
    command_start = True
    relative_allowed = True
    for token in tokens:
        if token and all(char in ";&|()" for char in token):
            command_start = True
            relative_allowed = token in {";", "&&", "||", "|", "&"}
        elif command_start and token in {"if", "then", "do", "elif", "while", "until", "!", "exec"}:
            continue
        elif command_start and re.match(r"^[A-Za-z_][A-Za-z_0-9]*=", token):
            continue
        elif command_start:
            absolute = re.match(r"^(?:/|\./|\.\./)[A-Za-z0-9_.-]", token)
            relative = relative_allowed and re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+", token)
            if (absolute or relative) and token not in {"/.", "/..", ".", ".."}:
                return True
            command_start = False
    return False


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
            dynamic_source = re.search(
                r"(?:^\s*|[;&|()]\s*|\b(?:if|then|do|elif|while|until)\s+)(?:source|\.)\s+[\"']?[^\s;&|()]+", line)
            external_script = re.search(
                r"(?:^\s*|[;&|()]\s*|\b(?:if|then|do|elif|while|until)\s+)(?:bash|sh)\s+(?:-[A-Za-z0-9-]+\s+)*[\"']?[^-\s;&|()]+", line)
            inherited_shell = re.search(
                r"(?:^\s*|[;&|()]\s*|\b(?:if|then|do|elif|while|until)\s+)(?:bash|sh)(?:\s+-[A-Za-z0-9-]+)*(?:\s*(?:[;&|)]|$))", line)
            direct_path = _direct_path_command(line)
            if dynamic_command:
                issues.append(f"{path}:{number}: dynamic command requires review")
            elif dynamic_executable or dynamic_source or external_script or inherited_shell or direct_path:
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
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "join" and len(node.args) == 1 and not node.keywords
            and isinstance(node.args[0], (ast.List, ast.Tuple))):
        separator = _literal_string(node.func.value)
        parts = [_literal_string(item) for item in node.args[0].elts]
        if separator is not None and all(part is not None for part in parts):
            return separator.join(parts)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _literal_string(node.left), _literal_string(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _scoped_names(tree, source, path):
    """Give lexical bindings distinct names before conservative dataflow analysis."""
    root = symtable.symtable(source, path, "exec")

    class ScopedNames(ast.NodeTransformer):
        def __init__(self):
            self.stack = [root]
            self.ids = {id(root): "module"}
            self.next_id = 0
            self.used = set()
            self.children = {}

        def child(self, name, lineno):
            table = next(item for item in reversed(self.stack) if not isinstance(item, dict))
            candidates = self.children.setdefault(id(table), table.get_children())
            for candidate in candidates:
                if (id(candidate) not in self.used and candidate.get_name() == name
                        and candidate.get_lineno() == lineno):
                    self.used.add(id(candidate))
                    self.next_id += 1
                    self.ids[id(candidate)] = str(self.next_id)
                    return candidate
            return None

        def name(self, name):
            free = False
            for table in reversed(self.stack):
                if isinstance(table, dict):
                    if name in table:
                        return table[name]
                    continue
                if free and table.get_type() == "class":
                    continue
                try:
                    symbol = table.lookup(name)
                except KeyError:
                    continue
                if symbol.is_global():
                    return name
                if symbol.is_free() or symbol.is_nonlocal():
                    free = True
                    continue
                if symbol.is_local() or symbol.is_parameter():
                    if table.get_type() == "module":
                        return name
                    return name + "__scope_" + self.ids[id(table)]
            return name

        def visit_Name(self, node):
            node.id = self.name(node.id)
            return node

        def visit_arg(self, node):
            node.arg = self.name(node.arg)
            if node.annotation:
                node.annotation = self.visit(node.annotation)
            return node

        def function(self, node, name):
            node.decorator_list = [self.visit(item) for item in node.decorator_list] if hasattr(node, "decorator_list") else []
            defaults = [self.visit(item) for item in node.args.defaults]
            kw_defaults = [self.visit(item) if item else None for item in node.args.kw_defaults]
            arguments = (node.args.posonlyargs + node.args.args + node.args.kwonlyargs
                         + ([node.args.vararg] if node.args.vararg else [])
                         + ([node.args.kwarg] if node.args.kwarg else []))
            annotations = [self.visit(arg.annotation) if arg.annotation else None for arg in arguments]
            for arg in arguments:
                arg.annotation = None
            if getattr(node, "returns", None):
                node.returns = self.visit(node.returns)
            node.args.defaults = []
            node.args.kw_defaults = []
            table = self.child(name, node.lineno)
            if table is None:
                raise ValueError("cannot resolve Python lexical scope")
            self.stack.append(table)
            node.args = self.visit(node.args)
            for arg, annotation in zip(arguments, annotations):
                arg.annotation = annotation
            node.args.defaults = defaults
            node.args.kw_defaults = kw_defaults
            if isinstance(node.body, list):
                node.body = [self.visit(item) for item in node.body]
            else:
                node.body = self.visit(node.body)
            self.stack.pop()
            return node

        def visit_FunctionDef(self, node):
            return self.function(node, node.name)

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Lambda(self, node):
            return self.function(node, "lambda")

        def visit_ClassDef(self, node):
            node.decorator_list = [self.visit(item) for item in node.decorator_list]
            node.bases = [self.visit(item) for item in node.bases]
            node.keywords = [self.visit(item) for item in node.keywords]
            table = self.child(node.name, node.lineno)
            if table is None:
                raise ValueError("cannot resolve Python lexical scope")
            self.stack.append(table)
            node.body = [self.visit(item) for item in node.body]
            self.stack.pop()
            return node

        def comprehension(self, node, name):
            node.generators[0].iter = self.visit(node.generators[0].iter)
            table = self.child(name, node.lineno)
            if table is None:
                self.next_id += 1
                suffix = str(self.next_id)
                names = {item.id for generator in node.generators
                         for item in ast.walk(generator.target) if isinstance(item, ast.Name)}
                table = {item: item + "__scope_" + suffix for item in names}
            self.stack.append(table)
            for index, generator in enumerate(node.generators):
                generator.target = self.visit(generator.target)
                if index:
                    generator.iter = self.visit(generator.iter)
                generator.ifs = [self.visit(item) for item in generator.ifs]
            for field in ("elt", "key", "value"):
                if hasattr(node, field):
                    setattr(node, field, self.visit(getattr(node, field)))
            self.stack.pop()
            return node

        def visit_ListComp(self, node):
            return self.comprehension(node, "listcomp")

        def visit_SetComp(self, node):
            return self.comprehension(node, "setcomp")

        def visit_DictComp(self, node):
            return self.comprehension(node, "dictcomp")

        def visit_GeneratorExp(self, node):
            return self.comprehension(node, "genexpr")

        def visit_ImportFrom(self, node):
            for alias in node.names:
                if alias.name != "*":
                    alias.asname = self.name(alias.asname or alias.name)
            return node

        def visit_Import(self, node):
            for alias in node.names:
                original = alias.asname or alias.name.split(".")[0]
                renamed = self.name(original)
                if renamed != original:
                    alias.asname = renamed
            return node

        def visit_MatchAs(self, node):
            if node.pattern:
                node.pattern = self.visit(node.pattern)
            if node.name:
                node.name = self.name(node.name)
            return node

        def visit_MatchStar(self, node):
            if node.name:
                node.name = self.name(node.name)
            return node

        def visit_MatchMapping(self, node):
            self.generic_visit(node)
            if node.rest:
                node.rest = self.name(node.rest)
            return node

    return ScopedNames().visit(tree)


def _python(path, source):
    issues = []
    try:
        tree = _scoped_names(ast.parse(source, filename=path), source, path)
    except (SyntaxError, ValueError):
        return [f"{path}: invalid Python source"]
    tree_nodes = tuple(ast.walk(tree))
    calls = tuple(node for node in tree_nodes if isinstance(node, ast.Call))
    assignments = tuple(node for node in tree_nodes if isinstance(node, (ast.Assign, ast.AnnAssign)))
    bindings = tuple(node for node in tree_nodes if isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension, ast.withitem)))
    functions = tuple(node for node in tree_nodes if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)))
    matches = tuple(node for node in tree_nodes if isinstance(node, ast.Match))
    named_assignments = tuple(node for node in tree_nodes if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)))
    imported_calls = {alias.asname or alias.name
                      for node in tree_nodes
                      if isinstance(node, ast.ImportFrom) and node.module == "subprocess"
                      for alias in node.names
                      if alias.name in {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"}}
    subprocess_modules = {alias.asname or alias.name for node in tree_nodes
                          if isinstance(node, ast.Import) for alias in node.names
                          if alias.name == "subprocess"} | {"subprocess"}
    os_modules = {alias.asname or alias.name for node in tree_nodes
                  if isinstance(node, ast.Import) for alias in node.names
                  if alias.name == "os"} | {"os"}
    os_executables = {alias.asname or alias.name for node in tree_nodes
                      if isinstance(node, ast.ImportFrom) and node.module == "os"
                      for alias in node.names
                      if alias.name.startswith(("exec", "spawn"))}
    os_systems = {alias.asname or alias.name for node in tree_nodes
                  if isinstance(node, ast.ImportFrom) and node.module == "os"
                      for alias in node.names if alias.name in {"system", "popen"}}
    dynamic_code = {"exec", "eval"}
    for imported in (node for node in tree_nodes if isinstance(node, ast.ImportFrom)
                     and node.module in {"os", "subprocess"}):
        if any(alias.name == "*" for alias in imported.names):
            issues.append(f"{path}:{imported.lineno}: unclassified Python executable")
    callable_aliases = set(imported_calls)
    callable_containers = set()
    module_containers = set()
    callable_attributes = set()
    aliases = set()
    changed = True
    while changed:
        changed = False
        for call in calls:
            if (isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name)
                    and call.func.attr in {'append', 'extend', 'insert', 'add', 'update'}):
                if any(isinstance(item, ast.Attribute) and isinstance(item.value, ast.Name)
                       and item.value.id in subprocess_modules | os_modules for arg in call.args for item in ast.walk(arg)):
                    if call.func.value.id not in callable_containers:
                        callable_containers.add(call.func.value.id)
                        changed = True
        for assignment in assignments:
            targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
            value = assignment.value
            if value is None:
                continue
            if isinstance(value, ast.Call) and isinstance(value.func, ast.Lambda):
                value = value.func.body
            relevant = any((_literal_string(item) is not None and "validate-contracts." in _literal_string(item)) or (isinstance(item, ast.Name) and item.id in aliases) for item in ast.walk(value))
            callable_value = ((isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name)
                               and value.value.id in subprocess_modules and value.attr in {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"})
                              or (isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
                                  and value.func.id == "getattr" and value.args
                                  and isinstance(value.args[0], ast.Name) and value.args[0].id in subprocess_modules)
                              or (isinstance(value, ast.Name) and value.id in callable_aliases))
            executable_value = ((isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name)
                                 and value.value.id in os_modules and value.attr.startswith(("exec", "spawn")))
                                or (isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
                                    and value.func.id == "getattr" and value.args
                                    and isinstance(value.args[0], ast.Name) and value.args[0].id in os_modules)
                                or (isinstance(value, ast.Name) and value.id in os_executables))
            system_value = ((isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name)
                             and value.value.id in os_modules and value.attr in {"system", "popen"})
                            or (isinstance(value, ast.Name) and value.id in os_systems))
            dynamic_code_value = isinstance(value, ast.Name) and value.id in dynamic_code
            contained_callable = (isinstance(value, (ast.Dict, ast.List, ast.Tuple, ast.Set)) and any(
                (isinstance(item, ast.Attribute) and isinstance(item.value, ast.Name)
                 and ((item.value.id in subprocess_modules and item.attr in {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"})
                      or (item.value.id in os_modules and (item.attr.startswith(("exec", "spawn")) or item.attr in {"system", "popen"}))))
                or (isinstance(item, ast.Name) and item.id in callable_aliases | os_systems | os_executables | dynamic_code)
                for item in ast.walk(value))) or (isinstance(value, ast.Name) and value.id in callable_containers)
            contained_module = (isinstance(value, (ast.Dict, ast.List, ast.Tuple, ast.Set)) and any(
                isinstance(item, ast.Name) and item.id in subprocess_modules | os_modules | module_containers
                for item in ast.walk(value))) or (isinstance(value, ast.Name) and value.id in module_containers)
            def module_bindings(target, expression):
                if isinstance(target, ast.Name) and isinstance(expression, ast.Name):
                    return [(target, expression)]
                if isinstance(target, (ast.Tuple, ast.List)) and isinstance(expression, (ast.Tuple, ast.List)):
                    return [pair for left, right in zip(target.elts, expression.elts)
                            for pair in module_bindings(left, right)]
                return []
            for target in targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                    key = (target.value.id, target.attr)
                    if (callable_value or executable_value or system_value or dynamic_code_value) and key not in callable_attributes:
                        callable_attributes.add(key)
                        changed = True
                if (isinstance(target, ast.Name) and isinstance(value, ast.Call)
                        and ((isinstance(value.func, ast.Attribute) and value.func.attr == 'import_module')
                             or (isinstance(value.func, ast.Name) and value.func.id == '__import__'))):
                    imported = _literal_string(value.args[0]) if value.args else None
                    for module, names in (('subprocess', subprocess_modules), ('os', os_modules)):
                        if (imported is None or imported == module) and target.id not in names:
                            names.add(target.id)
                            changed = True
                if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                    if (callable_value or executable_value or system_value or dynamic_code_value or contained_callable) and target.value.id not in callable_containers:
                        callable_containers.add(target.value.id)
                        changed = True
                    if isinstance(value, ast.Name) and value.id in subprocess_modules | os_modules | module_containers and target.value.id not in module_containers:
                        module_containers.add(target.value.id)
                        changed = True
                for destination, expression in module_bindings(target, value):
                    for modules in (subprocess_modules, os_modules):
                        if expression.id in modules and destination.id not in modules:
                            modules.add(destination.id)
                            changed = True
                for item in ast.walk(target):
                    if isinstance(item, ast.Name):
                        if contained_callable and item.id not in callable_containers:
                            callable_containers.add(item.id)
                            changed = True
                        if contained_module and item.id not in module_containers:
                            module_containers.add(item.id)
                            changed = True
                if relevant and isinstance(target, ast.Name) and target.id not in aliases:
                    aliases.add(target.id)
                    changed = True
                if callable_value and isinstance(target, ast.Name) and target.id not in callable_aliases:
                    callable_aliases.add(target.id)
                    changed = True
                if executable_value and isinstance(target, ast.Name) and target.id not in os_executables:
                    os_executables.add(target.id)
                    changed = True
                if system_value and isinstance(target, ast.Name) and target.id not in os_systems:
                    os_systems.add(target.id)
                    changed = True
                if dynamic_code_value and isinstance(target, ast.Name) and target.id not in dynamic_code:
                    dynamic_code.add(target.id)
                    changed = True
    static_strings = {}
    historical_strings = {}
    def static_string(node):
        if isinstance(node, ast.Name):
            return static_strings.get(node.id)
        if isinstance(node, ast.JoinedStr):
            pieces = [static_string(part.value if isinstance(part, ast.FormattedValue) else part)
                      for part in node.values]
            return "".join(pieces) if all(piece is not None for piece in pieces) else None
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left, right = static_string(node.left), static_string(node.right)
            return left + right if left is not None and right is not None else None
        return _literal_string(node)

    reference_aliases = set()
    partial_aliases = set()
    nodes = sorted(tree_nodes, key=lambda node: (getattr(node, "lineno", 0), getattr(node, "col_offset", 0)))
    for assignment in nodes:
        if isinstance(assignment, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
            targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
            value = static_string(assignment.value) if assignment.value is not None else None
        elif isinstance(assignment, ast.AugAssign) and isinstance(assignment.op, ast.Add):
            targets = [assignment.target]
            left, right = static_string(assignment.target), static_string(assignment.value)
            value = left + right if left is not None and right is not None else None
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                literal = _literal_string(assignment.value) if assignment.value is not None else None
                if literal and len(literal) >= 4 and literal in VALIDATOR:
                    partial_aliases.add(target.id)
                if value is None:
                    static_strings.pop(target.id, None)
                else:
                    static_strings[target.id] = value
                    historical_strings.setdefault(target.id, set()).add(value)
                    if VALIDATOR in value:
                        reference_aliases.add(target.id)
    def possible_strings(node):
        if isinstance(node, ast.Name):
            return historical_strings.get(node.id, set())
        if isinstance(node, ast.JoinedStr):
            parts = [possible_strings(part.value if isinstance(part, ast.FormattedValue) else part)
                     for part in node.values]
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            parts = [possible_strings(node.left), possible_strings(node.right)]
        else:
            literal = _literal_string(node)
            return {literal} if literal is not None else set()
        result = {""}
        for part in parts:
            if len(result) * len(part) > 4096:
                return {VALIDATOR}
            result = {left + right for left in result for right in part}
        return result

    saturated = set()
    changed = True
    while changed:
        changed = False
        for assignment in nodes:
            if isinstance(assignment, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
                targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
                values = possible_strings(assignment.value) if assignment.value is not None else set()
            elif isinstance(assignment, ast.AugAssign) and isinstance(assignment.op, ast.Add):
                targets = [assignment.target]
                left, right = possible_strings(assignment.target), possible_strings(assignment.value)
                values = ({a + b for a in left for b in right}
                          if len(left) * len(right) <= 4096 else {VALIDATOR})
            else:
                continue
            for target in targets:
                if not isinstance(target, ast.Name) or target.id in saturated:
                    continue
                previous = historical_strings.get(target.id, set())
                combined = previous | values
                if len(combined) > 64 or any(len(value) > 4096 for value in combined):
                    historical_strings[target.id] = {VALIDATOR}
                    saturated.add(target.id)
                    reference_aliases.add(target.id)
                    changed = True
                elif combined != previous:
                    historical_strings[target.id] = combined
                    changed = True
                if any(VALIDATOR in value for value in combined):
                    reference_aliases.add(target.id)

    changed = True
    while changed:
        changed = False
        for function in functions:
            parameters = function.args.posonlyargs + function.args.args
            defaults = list(zip(parameters[len(parameters) - len(function.args.defaults):], function.args.defaults))
            defaults += list(zip(function.args.kwonlyargs, function.args.kw_defaults))
            for parameter, default in defaults:
                if default is not None and any(
                    (_literal_string(item) is not None and VALIDATOR in _literal_string(item))
                    or (isinstance(item, ast.Name) and item.id in reference_aliases)
                    for item in ast.walk(default)
                ) and parameter.arg not in reference_aliases:
                    reference_aliases.add(parameter.arg)
                    changed = True
        for match in matches:
            if any(
                (_literal_string(item) is not None and VALIDATOR in _literal_string(item))
                or (isinstance(item, ast.Name) and item.id in reference_aliases)
                for item in ast.walk(match.subject)
            ):
                for case in match.cases:
                    for pattern in ast.walk(case.pattern):
                        name = (pattern.name if isinstance(pattern, (ast.MatchAs, ast.MatchStar))
                                else pattern.rest if isinstance(pattern, ast.MatchMapping) else None)
                        if name is not None and name not in reference_aliases:
                            reference_aliases.add(name)
                            changed = True
        for binding in bindings:
            if isinstance(binding, (ast.For, ast.AsyncFor, ast.comprehension)):
                value, target = binding.iter, binding.target
            elif isinstance(binding, ast.withitem) and binding.optional_vars is not None:
                value, target = binding.context_expr, binding.optional_vars
            else:
                continue
            if not any(isinstance(item, ast.Call) for item in ast.walk(value)) and any(
                (_literal_string(item) is not None and VALIDATOR in _literal_string(item))
                or (isinstance(item, ast.Name) and item.id in reference_aliases)
                for item in ast.walk(value)
            ):
                for item in ast.walk(target):
                    if isinstance(item, ast.Name) and item.id not in reference_aliases:
                        reference_aliases.add(item.id)
                        changed = True
        for assignment in named_assignments:
            value = assignment.value
            if value is None or any(isinstance(item, ast.Call) for item in ast.walk(value)):
                continue
            relevant = any((_literal_string(item) is not None and VALIDATOR in _literal_string(item))
                           or (isinstance(item, ast.Name) and item.id in reference_aliases)
                           for item in ast.walk(value))
            targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
            for target in targets:
                for item in ast.walk(target):
                    if relevant and isinstance(item, ast.Name) and item.id not in reference_aliases:
                        reference_aliases.add(item.id)
                        changed = True
    for node in calls:
        fn = node.func
        if (isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name)
                and (fn.value.id, fn.attr) in callable_attributes):
            issues.append(f"{path}:{node.lineno}: unclassified Python executable")
            continue
        if isinstance(fn, ast.Subscript) and isinstance(fn.value, ast.Name) and fn.value.id in callable_containers:
            issues.append(f"{path}:{node.lineno}: unclassified Python executable")
            continue
        if (isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Subscript)
                and isinstance(fn.value.value, ast.Name) and fn.value.value.id in module_containers):
            issues.append(f"{path}:{node.lineno}: unclassified Python executable")
            continue
        name = fn.attr if isinstance(fn, ast.Attribute) else fn.id if isinstance(fn, ast.Name) else ""
        indirect = (isinstance(fn, ast.Call) and isinstance(fn.func, ast.Name) and fn.func.id == "getattr"
                    and fn.args and isinstance(fn.args[0], ast.Name) and fn.args[0].id in subprocess_modules)
        indirect_os = (isinstance(fn, ast.Call) and isinstance(fn.func, ast.Name) and fn.func.id == "getattr"
                       and fn.args and isinstance(fn.args[0], ast.Name) and fn.args[0].id in os_modules)
        if indirect:
            name = "indirect_subprocess"
        os_exec = ((isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name)
                    and fn.value.id in os_modules and fn.attr.startswith(("exec", "spawn")))
                   or (isinstance(fn, ast.Name) and fn.id in os_executables))
        if os_exec or indirect_os:
            issues.append(f"{path}:{node.lineno}: unclassified Python executable")
            continue
        subprocess_call = (isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name)
                           and fn.value.id in subprocess_modules and name in {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"})
        known_call = (subprocess_call or indirect or (isinstance(fn, ast.Name) and name in callable_aliases | os_systems | dynamic_code)
                      or (isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name)
                          and fn.value.id in os_modules and name in {"system", "popen"}))
        system_call = ((isinstance(fn, ast.Name) and name in os_systems)
                       or (isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name)
                           and fn.value.id in os_modules and name in {"system", "popen"}))
        if not known_call:
            arguments = list(node.args) + [keyword.value for keyword in node.keywords]
            if any(any(VALIDATOR in value for value in possible_strings(item))
                   or (isinstance(item, ast.Name) and item.id in reference_aliases | partial_aliases)
                   for argument in arguments for item in ast.walk(argument)):
                issue = f"{path}:{node.lineno}: unclassified Python reference"
                if issue not in issues:
                    issues.append(issue)
            continue
        extra_arguments = list(node.args[1:]) + [keyword.value for keyword in node.keywords if keyword.arg != "args"]
        if any(any(VALIDATOR in value for value in possible_strings(item))
               or (isinstance(item, ast.Name) and item.id in aliases | reference_aliases | partial_aliases | {"validator"})
               for argument in extra_arguments for item in ast.walk(argument)):
            issues.append(f"{path}:{node.lineno}: unclassified Python argument")
        keyword_args = [keyword.value for keyword in node.keywords if keyword.arg == "args"]
        commands = ([node.args[0]] if node.args else []) + keyword_args
        if any(keyword.arg in ("executable", None) for keyword in node.keywords):
            issues.append(f"{path}:{node.lineno}: subprocess executable override requires review")
            continue
        if any(keyword.arg == "shell" and not (isinstance(keyword.value, ast.Constant)
                                                  and keyword.value.value is False)
               for keyword in node.keywords):
            issues.append(f"{path}:{node.lineno}: subprocess shell mode requires review")
            continue
        references = [item for command in commands for item in ast.walk(command) if
                      any(VALIDATOR in value for value in possible_strings(item))
                      or (isinstance(item, ast.Name) and item.id in aliases | reference_aliases | partial_aliases | {"validator"})]
        if not references:
            if name in dynamic_code or system_call:
                issues.append(f"{path}:{node.lineno}: unclassified Python executable")
            def unknown_executable(command):
                if not isinstance(command, (ast.List, ast.Tuple)) or not command.elts:
                    return True
                values = [_literal_string(item) for item in command.elts]
                if values[0] is None:
                    return True
                executable = values[0].rsplit('/', 1)[-1]
                if ('/' in values[0] or executable.endswith(('.sh', '.py'))) and executable not in {'bash', 'sh'} and not re.fullmatch(r'python(?:[0-9]+(?:\.[0-9]+)*)?', executable):
                    return True
                if executable == 'env':
                    # Environment options and assignments can change how the next
                    # executable is selected; require review of the complete argv.
                    return True
                if executable in {'bash', 'sh'} or re.fullmatch(r'python(?:[0-9]+(?:\.[0-9]+)*)?', executable):
                    safe_options = ({'-e', '-l', '-u', '-x', '-n'} if executable in {'bash', 'sh'}
                                    else {'-u', '-B', '-E', '-I', '-O', '-OO', '-s', '-S'})
                    if not (executable in {'bash', 'sh'} and '-n' in values[1:]) and any(keyword.arg in {'input', 'stdin'} for keyword in node.keywords):
                        return True
                    for value in values[1:]:
                        if value is None or value in {'-c', '-m', '--command'}:
                            return True
                        if value.startswith('-') and value != '-' and value not in safe_options:
                            return True
                        if not value.startswith('-') or value == '-':
                            return True
                    return not (executable in {'bash', 'sh'} and '-n' in values[1:])
                return True
            if ((subprocess_call or name in callable_aliases)
                    and len(commands) == 1 and unknown_executable(commands[0])):
                issues.append(f"{path}:{node.lineno}: unclassified Python executable")
            continue
        if len(commands) != 1:
            issues.append(f"{path}:{node.lineno}: ambiguous Python invocation")
            continue
        arg = commands[0]
        if indirect:
            issues.append(f"{path}:{node.lineno}: unclassified indirect subprocess invocation")
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


def _inventory_digest(root, sources):
    """Bind a reviewed dynamic call to the complete source inventory."""
    base = Path(root).resolve()
    digest = hashlib.sha256()
    for name, expected in sorted(sources.items()):
        path = base / name
        data = path.read_bytes()
        if data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n") != expected:
            raise ValueError("source changed during inventory")
        if name == "tests/fixtures/validator-runtime/source_guard.py":
            data, count = re.subn(
                rb'(hashlib\.sha256\(data\)\.hexdigest\(\) != ")[0-9a-f]{64}(":)',
                rb'\g<1>' + b'0' * 64 + rb'\g<2>', data,
            )
            if count != 1:
                raise ValueError("invalid manifest digest marker")
        encoded = name.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()



@lru_cache(maxsize=32)
def _function_contexts(path, source):
    tree = ast.parse(source, filename=path)
    return [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _context(path, source, number):
    lines = source.splitlines()
    if number < 1 or number > len(lines):
        raise ValueError("diagnostic line is outside the source")
    if path.endswith(".py"):
        functions = [node for node in _function_contexts(path, source)
                     if node.lineno <= number <= node.end_lineno]
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
    try:
        inventory_digest = _inventory_digest(root, sources) if any(
            isinstance(entry, dict) and "inventory_sha256" in entry for entry in classified
        ) else None
    except (OSError, UnicodeError, ValueError, OverflowError):
        return issues + ["cannot verify classified source inventory"]
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
            if "inventory_sha256" in entry and entry["inventory_sha256"] != inventory_digest:
                return False
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
        if hashlib.sha256(data).hexdigest() != "07cc3016ac3fb24284441aab55b1a2ff7ffede3f4a0614e8aa55ae7419ce5f06":
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
