#!/usr/bin/env python3
"""Reject unclassified Python executable forms referencing the validator."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "source_guard", ROOT / "tests/fixtures/validator-runtime/source_guard.py"
)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class UnknownExecutableForms(unittest.TestCase):
    def assert_rejected(self, statement):
        path = "tests/example.py"
        violations = guard.inspect_sources({path: "import os\n" + statement + "\n"})
        self.assertTrue(violations, statement)
        self.assertTrue(any(path in str(item) for item in violations))

    def test_dynamic_shell_strings_require_review(self):
        for statement in (
            'os.system(\'bash "$TARGET"\')',
            "os.popen('bash $(command)')",
            "os.system('bash `command`')",
            'exec(\'os.system("bash $TARGET")\')',
            'eval(\'os.system("bash $TARGET")\')',
            "subprocess.run(['bash', '/tmp/payload.sh'])",
            "subprocess.run(['python3', '/tmp/payload.py'])",
        ):
            with self.subTest(statement=statement):
                self.assert_rejected(statement)

    def test_dynamic_shell_source_requires_review(self):
        for source in ('source "$TARGET"\n', '. "$TARGET"\n'):
            with self.subTest(source=source):
                self.assertTrue(guard.inspect_sources({"tests/example.sh": source}))

    def test_external_program_and_stdin_require_review(self):
        for statement in (
            "subprocess.run(['bash'], input='echo test', text=True)",
            "subprocess.run(['python3'], stdin=stream)",
            "subprocess.run(['/tmp/payload.sh'])",
        ):
            with self.subTest(statement=statement):
                self.assert_rejected(statement)

    def test_shell_external_script_and_conditional_source_require_review(self):
        for source in (
            'if source "$TARGET"; then :; fi\n',
            'if . "$TARGET"; then :; fi\n',
            'source /tmp/payload.sh\n',
            'bash /tmp/payload.sh\n',
        ):
            with self.subTest(source=source):
                self.assertTrue(guard.inspect_sources({"tests/example.sh": source}))

    def test_inherited_interpreter_input_and_path_executable_require_review(self):
        for statement in (
            "subprocess.run(['bash'])",
            "subprocess.run(['python3'])",
            "subprocess.run(['payload'])",
        ):
            with self.subTest(statement=statement):
                self.assert_rejected(statement)

    def test_shell_interpreter_flags_and_inline_script_require_review(self):
        for source in (
            'bash -e /tmp/payload.sh\n',
            'sh -u /tmp/payload.sh\n',
            "sh -c 'echo test'\n",
        ):
            with self.subTest(source=source):
                self.assertTrue(guard.inspect_sources({"tests/example.sh": source}))

    def test_shell_inherited_input_and_direct_path_require_review(self):
        for source in (
            'bash < /tmp/payload.sh\n',
            'bash\n',
            'bash -e\n',
            '/tmp/payload.sh\n',
            'true; /tmp/payload.sh\n',
        ):
            with self.subTest(source=source):
                self.assertTrue(guard.inspect_sources({"tests/example.sh": source}))

    def test_execl_validator_reference_requires_review(self):
        self.assert_rejected("os.execl('/bin/bash', 'bash', 'scripts/validate-contracts.sh')")

    def test_execv_validator_reference_requires_review(self):
        self.assert_rejected("os.execv('/bin/bash', ['bash', 'scripts/validate-contracts.sh'])")

    def test_execv_validator_path_alias_requires_review(self):
        self.assert_rejected("p = 'scripts/validate-contracts.sh'\nos.execv('/bin/bash', ['bash', p])")

    def test_unknown_callable_validator_path_alias_requires_review(self):
        self.assert_rejected("p = 'scripts/validate-contracts.sh'\ncustom_runner(p)")

    def test_tuple_unpacked_path_requires_review(self):
        self.assert_rejected("p, = ('scripts/validate-contracts.sh',)\nos.execv('/bin/bash', ['bash', p])")

    def test_nested_list_unpacked_path_requires_review(self):
        self.assert_rejected("[other, [p]] = ['ignored', ['scripts/validate-contracts.sh']]\ncustom_runner(p)")

    def test_chained_unpacked_path_requires_review(self):
        self.assert_rejected("p, = ('scripts/validate-contracts.sh',)\nq = p\ncustom_runner(q)")

    def test_assignment_expression_path_requires_review(self):
        self.assert_rejected("(p := 'scripts/validate-contracts.sh')\ncustom_runner(p)")

    def test_starred_unpacked_path_requires_review(self):
        self.assert_rejected("*paths, = ['scripts/validate-contracts.sh']\ncustom_runner(paths)")

    def test_subprocess_unpacked_path_requires_review(self):
        self.assert_rejected("p, = ('scripts/validate-contracts.sh',)\nsubprocess.run(['bash', p])")

    def test_default_parameter_path_requires_review(self):
        self.assert_rejected("def launch(p='scripts/validate-contracts.sh'):\n    os.execv('/bin/bash', ['bash', p])\nlaunch()")

    def test_known_name_with_validator_in_later_argument_requires_review(self):
        self.assert_rejected("def run(exe, script):\n    os.execv(exe, ['bash', script])\nrun('/bin/bash', 'scripts/validate-contracts.sh')")

    def test_known_name_with_validator_in_keyword_requires_review(self):
        self.assert_rejected("run('/bin/bash', script='scripts/validate-contracts.sh')")

    def test_for_loop_path_requires_review(self):
        self.assert_rejected("for p in ['scripts/validate-contracts.sh']:\n    os.execv('/bin/bash', ['bash', p])")

    def test_comprehension_path_requires_review(self):
        self.assert_rejected("[custom_runner(p) for p in ['scripts/validate-contracts.sh']]")

    def test_async_for_path_requires_review(self):
        self.assert_rejected("async def f():\n    async for p in ['scripts/validate-contracts.sh']:\n        custom_runner(p)")

    def test_match_capture_path_requires_review(self):
        self.assert_rejected("match 'scripts/validate-contracts.sh':\n    case p: custom_runner(p)")

    def test_augmented_path_requires_review(self):
        self.assert_rejected("p = 'scripts/'\np += 'validate-contracts.sh'\nos.execv('/bin/bash', ['bash', p])")

    def test_split_augmented_path_requires_review(self):
        self.assert_rejected("p = 'scripts/validate-'\np += 'contracts.sh'\ncustom_runner(p)")

    def test_concatenated_alias_path_requires_review(self):
        self.assert_rejected("a = 'scripts/validate-'\nb = 'contracts.sh'\np = a + b\ncustom_runner(p)")

    def test_formatted_alias_path_requires_review(self):
        self.assert_rejected("a = 'scripts/validate-'\np = f'{a}contracts.sh'\ncustom_runner(p)")

    def test_composed_direct_argument_requires_review(self):
        self.assert_rejected("a = 'scripts/validate-'\nb = 'contracts.sh'\ncustom_runner(a + b)")

    def test_joined_literal_reference_requires_review(self):
        self.assert_rejected("custom_runner(''.join(['validate-', 'contracts.sh']))")

    def test_later_focused_flag_assignment_does_not_authorize_call(self):
        self.assert_rejected("flag = '--wrong'\nsubprocess.run(['bash', 'scripts/validate-contracts.sh', flag])\nflag = '--hygiene-only'")

    def test_other_scope_focused_flag_does_not_authorize_call(self):
        self.assert_rejected("flag = '--wrong'\nsubprocess.run(['bash', 'scripts/validate-contracts.sh', flag])\ndef other():\n    flag = '--hygiene-only'")

    def test_variable_focused_flag_requires_review(self):
        self.assert_rejected("flag = '--hygiene-only'\nsubprocess.run(['bash', 'scripts/validate-contracts.sh', flag])")

    def test_later_reassignment_does_not_hide_composed_path(self):
        self.assert_rejected("a='validate-'\nb='contracts.sh'\ncustom_runner(a+b)\nb='other'")

    def test_later_suffix_reassignment_does_not_hide_path(self):
        self.assert_rejected("a='scripts/validate-contracts'\nb='.sh'\nos.execv('/bin/bash',['bash',a+b])\nb='.txt'")

    def test_other_scope_assignment_does_not_hide_composed_alias(self):
        self.assert_rejected("a='scripts/validate-contracts'\nb='.sh'\ndef unrelated():\n    b='.txt'\np=a+b\ncustom_runner(p)")

    def test_forward_global_values_do_not_hide_composed_alias(self):
        self.assert_rejected("def launch():\n    p=a+b\n    custom_runner(p)\na='scripts/validate-contracts'\nb='.sh'\nlaunch()")

    def test_unknown_os_executable_requires_review(self):
        self.assert_rejected("os.execv(executable, args)")

    def test_unknown_subprocess_argv_requires_review(self):
        self.assert_rejected("subprocess.run(args)")

    def test_unknown_subprocess_executable_in_list_requires_review(self):
        self.assert_rejected("subprocess.run([executable])")

    def test_unknown_interpreter_script_requires_review(self):
        self.assert_rejected("subprocess.run(['bash', script])")

    def test_unknown_nested_shell_command_requires_review(self):
        self.assert_rejected("subprocess.run(['bash', '-c', command])")

    def test_aliased_subprocess_module_requires_review(self):
        self.assert_rejected("import subprocess as sp\nx = sp\nx.run(args)")

    def test_aliased_os_module_requires_review(self):
        self.assert_rejected("import os as o\nx = o\nx.execv(executable, args)")

    def test_unpacked_module_alias_requires_review(self):
        self.assert_rejected("a, b = subprocess, 1\na.run(args)")

    def test_mapping_callable_alias_requires_review(self):
        self.assert_rejected("fns = {'launch': subprocess.run}\nfns['launch'](args)")

    def test_written_mapping_callable_requires_review(self):
        self.assert_rejected("fns = {}\nfns['launch'] = subprocess.run\nfns['launch'](args)")

    def test_module_in_container_requires_review(self):
        self.assert_rejected("fns = [subprocess]\nfns[0].run(args)")

    def test_appended_callable_requires_review(self):
        self.assert_rejected("fns = []\nfns.append(subprocess.run)\nfns[0](args)")

    def test_assigned_attribute_callable_requires_review(self):
        self.assert_rejected("c = C()\nc.run = subprocess.run\nc.run(args)")

    def test_import_module_alias_requires_review(self):
        self.assert_rejected("import importlib\ns = importlib.import_module('subprocess')\ns.run(args)")

    def test_immediately_called_lambda_returning_executable_requires_review(self):
        self.assert_rejected("import subprocess\nlaunch = (lambda: subprocess.run)()\nlaunch(args)")

    def test_os_popen_requires_review(self):
        self.assert_rejected("os.popen(command)")

    def test_unknown_interpreter_after_option_requires_review(self):
        for option in ('-e', '-l'):
            with self.subTest(option=option):
                self.assert_rejected(f"subprocess.run(['bash', '{option}', script])")

    def test_unknown_env_command_requires_review(self):
        self.assert_rejected("subprocess.run(['env', command])")

    def test_unknown_python_script_requires_review(self):
        self.assert_rejected("subprocess.run(['python3', script])")

    def test_unknown_exec_source_requires_review(self):
        self.assert_rejected("exec(source)")

    def test_unknown_eval_source_requires_review(self):
        self.assert_rejected("eval(source)")

    def test_exec_alias_requires_review(self):
        self.assert_rejected("launch = exec\nlaunch(source)")

    def test_executable_override_without_known_reference_requires_review(self):
        self.assert_rejected("subprocess.run(['ignored'], executable=executable)")

    def test_subprocess_keyword_unpack_requires_review(self):
        self.assert_rejected("subprocess.run(['ignored'], **options)")

    def test_shell_mode_without_known_reference_requires_review(self):
        self.assert_rejected("subprocess.run(['ignored'], shell=True)")

    def test_validator_interpreter_script_is_not_classified_as_safe(self):
        self.assert_rejected("subprocess.run(['bash', str(ROOT / 'scripts/validate-contracts.sh')])")

    def test_imported_execv_requires_review(self):
        self.assert_rejected("from os import execv as run\nrun(executable, args)")

    def test_indirect_execv_alias_requires_review(self):
        self.assert_rejected("launch = getattr(os, 'execv')\nlaunch(executable, args)")

    def test_system_alias_requires_review(self):
        self.assert_rejected("launch = os.system\nlaunch(command)")

    def test_star_import_requires_review(self):
        self.assert_rejected("from os import *\nexecv(executable, args)")

    def test_indirect_subprocess_alias_requires_review(self):
        self.assert_rejected("launch = getattr(subprocess, 'run')\nlaunch(args)")

    def test_locally_imported_subprocess_requires_review(self):
        self.assert_rejected("def launch():\n    import subprocess as sp\n    sp.run(args)")

    def test_global_default_reference_requires_review(self):
        self.assert_rejected("p = 'scripts/validate-contracts.sh'\ndef launch(p=p):\n    custom_runner(p)")

    def test_match_capture_in_function_requires_review(self):
        self.assert_rejected("def launch():\n    match 'scripts/validate-contracts.sh':\n        case p: custom_runner(p)")

    def test_parameter_shadows_global_reference(self):
        source = "p = 'scripts/validate-contracts.sh'\ndef other(p):\n    print(p)\n"
        self.assertEqual(guard.inspect_sources({'tests/example.py': source}), [])

    def test_nested_closure_reference_requires_review(self):
        self.assert_rejected("def outer():\n    p = 'scripts/validate-contracts.sh'\n    def inner():\n        custom_runner(p)")

    def test_nonlocal_reference_requires_review(self):
        self.assert_rejected("def outer():\n    p = 'scripts/validate-contracts.sh'\n    def inner():\n        nonlocal p\n        custom_runner(p)")

    def test_global_assignment_requires_review(self):
        self.assert_rejected("p = 'safe'\ndef launch():\n    global p\n    p = 'scripts/validate-contracts.sh'\n    custom_runner(p)")

    def test_comprehension_binding_does_not_escape(self):
        source = "[print(p) for p in ['scripts/validate-contracts.sh']]\ndef other(p):\n    print(p)\n"
        issues = guard.inspect_sources({'tests/example.py': source})
        self.assertFalse(any(':3:' in item for item in issues))

    def test_default_is_resolved_in_enclosing_scope(self):
        self.assert_rejected("p='scripts/validate-contracts.sh'\ndef launch(p=p):\n    custom_runner(p)")

    def test_class_scope_does_not_shadow_enclosing_closure(self):
        self.assert_rejected("def outer():\n    p='scripts/validate-contracts.sh'\n    class C:\n        p='safe'\n        def launch(self):\n            custom_runner(p)")

    def test_local_reference_does_not_taint_other_function(self):
        source = "def first():\n    private_path = 'scripts/validate-contracts.sh'\ndef second(private_path):\n    print(private_path)\n"
        self.assertEqual(guard.inspect_sources({'tests/example.py': source}), [])

    def test_global_reference_is_visible_in_function(self):
        self.assert_rejected("p = 'scripts/validate-contracts.sh'\ndef launch():\n    custom_runner(p)")

    def test_unknown_callable_validator_reference_requires_review(self):
        self.assert_rejected("custom_runner('scripts/validate-contracts.sh')")


class InventoryBoundClassification(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "scripts").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "scripts/validate-contracts.sh").write_text("#!/bin/sh\n")
        self.wrapper = self.root / "tests/wrapper.py"
        self.wrapper.write_text("def launch(args):\n    subprocess.run(args)\n")
        self.caller = self.root / "tests/caller.py"
        self.caller.write_text("launch(['safe'])\n")
        sources = guard.inventory_sources(self.root)
        source = sources["tests/wrapper.py"]
        container, context = guard._context("tests/wrapper.py", source, 2)
        self.entries = [{"path": "tests/wrapper.py", "statement": "    subprocess.run(args)",
                         "container": container, "context_sha256": guard._digest(context),
                         "detail": "unclassified Python executable", "count": 1,
                         "reason": "The caller inventory was reviewed.",
                         "inventory_sha256": guard._inventory_digest(self.root, sources)}]

    def test_reviewed_inventory_passes(self):
        self.assertEqual(guard.inspect_project(self.root, self.entries), [])

    def test_added_caller_invalidates_review(self):
        (self.root / "tests/new_caller.py").write_text("launch(['safe'])\n")
        self.assertTrue(guard.inspect_project(self.root, self.entries))

    def test_changed_caller_invalidates_review(self):
        self.caller.write_text("launch(['different'])\n")
        self.assertTrue(guard.inspect_project(self.root, self.entries))

    def test_deleted_caller_invalidates_review(self):
        self.caller.unlink()
        self.assertTrue(guard.inspect_project(self.root, self.entries))

    def test_changed_line_endings_invalidate_review(self):
        self.caller.write_bytes(b"launch(['safe'])\r\n")
        self.assertTrue(guard.inspect_project(self.root, self.entries))

    def test_changed_copied_helper_invalidates_review(self):
        helper = self.root / 'scripts/log-step.sh'
        helper.write_text('#!/bin/sh\nprintf safe\\n\n')
        self.entries[0]['dependencies'] = {'scripts/log-step.sh': guard.hashlib.sha256(helper.read_bytes()).hexdigest()}
        self.assertEqual(guard.inspect_project(self.root, self.entries), [])
        helper.write_text('#!/bin/sh\nbash scripts/validate-contracts.sh\n')
        self.assertTrue(guard.inspect_project(self.root, self.entries))

    def test_relocated_helper_calls_pin_executed_source(self):
        manifest = ROOT / 'tests/fixtures/validator-runtime/source_guard_exceptions.json'
        entries = json.loads(manifest.read_text())
        helpers = ('log-step.sh', 'sync.sh', 'link-skills.sh')
        for entry in entries:
            statement = entry.get('statement', '')
            if entry.get('container') == 'test_shell_paths_relocated_checkout_preserves_overrides' and 'bash "$source_tree/$script"' in statement:
                for helper in ('setup-new-project.sh', 'setup-umbrella.sh', 'setup-all-repos.sh'):
                    self.assertIn('scripts/' + helper, entry.get('dependencies', {}))
            for helper in helpers:
                if helper in statement and ('bash ' in statement or 'bash\\"' in statement):
                    with self.subTest(statement=statement, helper=helper):
                        self.assertIn('scripts/' + helper, entry.get('dependencies', {}))

    def test_only_manifest_digest_is_normalized(self):
        guard_path = self.root / "tests/fixtures/validator-runtime/source_guard.py"
        guard_path.parent.mkdir(parents=True)
        source = 'if hashlib.sha256(data).hexdigest() != "' + 'a' * 64 + '": pass\n'
        guard_path.write_text(source)
        original = guard._inventory_digest(self.root, guard.inventory_sources(self.root))
        guard_path.write_text(source.replace('a' * 64, 'b' * 64))
        self.assertEqual(original, guard._inventory_digest(self.root, guard.inventory_sources(self.root)))
        guard_path.write_text(source + '# changed\n')
        self.assertNotEqual(original, guard._inventory_digest(self.root, guard.inventory_sources(self.root)))


if __name__ == "__main__":
    unittest.main()
