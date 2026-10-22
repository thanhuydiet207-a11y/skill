import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from omega.process import execute
from omega.context import packet
from omega.safety import artifact_path
import omega.__main__ as app


class ProcessSafety(unittest.TestCase):
    def test_flood_is_killed_without_unbounded_spool(self):
        r=execute([sys.executable,'-c','import os\nwhile True: os.write(1,b"x"*4096)'],app.ROOT,
                  timeout=3,capture_bytes=1024,max_output_bytes=8192)
        self.assertEqual(r['exit_code'],125)
        self.assertTrue(r['output_limit_exceeded']);self.assertTrue(r['truncated'])
        self.assertLessEqual(len(r['output']),1024)

    def test_missing_executable_is_reported(self):
        r=execute(['/definitely/missing/omega-executable'],app.ROOT)
        self.assertEqual(r['exit_code'],127)

    def test_child_inheriting_stdout_is_bounded(self):
        r=execute([sys.executable,'-c','import subprocess,sys; subprocess.Popen([sys.executable,"-c","import time;time.sleep(10)"])'],
                  app.ROOT,timeout=0.1)
        self.assertEqual(r['exit_code'],124)
        self.assertTrue(r['timed_out'])

    def test_invalid_limits_refused(self):
        for argv in ([],['echo',''],['echo','\0'], 'echo hello'):
            with self.assertRaises(ValueError):execute(argv,app.ROOT)
        with self.assertRaises(ValueError):execute(['echo'],app.ROOT,timeout=-1)

    def test_capture_is_prefix_and_failure_exit_preserved(self):
        r=execute([sys.executable,'-c','print("0123456789");raise SystemExit(9)'],app.ROOT,capture_bytes=5)
        self.assertEqual(r['output'],'01234');self.assertEqual(r['exit_code'],9)
        self.assertTrue(r['truncated'])


class PolicySafety(unittest.TestCase):
    def test_empty_or_missing_gate_fails_before_execution(self):
        for gates in ({},{'build':['echo','ok']},{'build':[]}):
            with patch.object(app,'CONFIG',{'gates':gates,'limits':app.CONFIG['limits']}),patch.object(app,'run') as run:
                with self.assertRaises(ValueError):app.gates()
                run.assert_not_called()

    def test_invalid_later_gate_prevents_any_execution(self):
        c={**app.CONFIG,'gates':{**app.CONFIG['gates'],'extra':['echo',None]}}
        with patch.object(app,'CONFIG',c),patch.object(app,'run') as run:
            with self.assertRaises(ValueError):app.gates()
            run.assert_not_called()

    def test_private_alias_names_are_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'safe').write_text('not secret')
            (root/'.env').symlink_to(root/'safe')
            (root/'public-alias').symlink_to(root/'.env')
            for name in ('.env','public-alias'):
                with self.assertRaises(ValueError):packet(root,[name])

    def test_artifact_symlink_inside_repo_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'other').mkdir();(root/'.omega').symlink_to(root/'other')
            with self.assertRaises(ValueError):artifact_path(root,'.omega/evidence/x.json','evidence',False)

    def test_artifact_namespace_and_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ('other/x','.omega/memory/x','.omega/evidence/../../policy'):
                with self.assertRaises(ValueError):artifact_path(d,name,'evidence',False)

    def test_map_uses_nul_and_preserves_odd_filename(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);name=' space\nand quote".py';(root/name).write_text('pass')
            with patch.object(app,'ROOT',root),patch.object(app,'git',side_effect=[name+'\0','']) as git:
                result=app.inventory()
                self.assertEqual(result['files'][0]['path'],name)
                self.assertTrue(git.call_args_list[0].kwargs['raw'])


class TestRunnerSafety(unittest.TestCase):
    def execute_fixture(self,content):
        with tempfile.TemporaryDirectory() as d:
            if content is not None:(Path(d)/'test_fixture.py').write_text(content)
            return subprocess.run([sys.executable,'-m','omega.test_runner','--start',d],cwd=app.ROOT,text=True,capture_output=True)

    def test_no_tests_fails(self):self.assertEqual(self.execute_fixture(None).returncode,5)
    def test_all_skipped_fails(self):
        p=self.execute_fixture('import unittest\nclass T(unittest.TestCase):\n @unittest.skip("skip")\n def test_one(self): pass\n')
        self.assertEqual(p.returncode,5);self.assertIn('"skipped": 1',p.stdout)
    def test_expected_failure_alone_is_not_readiness(self):
        p=self.execute_fixture('import unittest\nclass T(unittest.TestCase):\n @unittest.expectedFailure\n def test_one(self): self.fail()\n')
        self.assertEqual(p.returncode,5);self.assertIn('"expected_failures": 1',p.stdout)


class EvidenceSafety(unittest.TestCase):
    def test_exit_zero_without_test_execution_is_not_ready(self):
        commands={name:[sys.executable,'-c','pass'] for name in app.CONFIG['gates']}
        with patch.object(app,'CONFIG',{**app.CONFIG,'gates':commands}):result=app.gates()
        self.assertTrue(all(r['exit_code']==0 for r in result['results']))
        self.assertFalse(result['passed']);self.assertIsNone(result['test_outcomes'])

    def test_test_marker_survives_truncated_prefix(self):
        from omega.records import test_outcomes
        counts={'run':1,'passed':1,'failed':0,'errors':0,'skipped':0,'expected_failures':0,'unexpected_successes':0}
        code='import json;print("x"*2000);print("OMEGA_TEST_RESULT "+json.dumps('+repr(counts)+'))'
        result=execute([sys.executable,'-c',code],app.ROOT,capture_bytes=1024)
        self.assertTrue(result['truncated']);self.assertEqual(test_outcomes(result),counts)

    def test_empty_failed_or_inconsistent_test_marker_rejected(self):
        from omega.records import test_outcomes
        zero={'run':0,'passed':0,'failed':0,'errors':0,'skipped':0,'expected_failures':0,'unexpected_successes':0}
        bad=[{},zero,{**zero,'passed':1},{**zero,'run':1,'passed':True},{**zero,'run':2,'passed':1,'failed':1}]
        for value in bad:
            self.assertIsNone(test_outcomes({'exit_code':0,'output':'OMEGA_TEST_RESULT '+json.dumps(value)}))
        self.assertIsNone(test_outcomes({'exit_code':False,'output':'anything'}))

    def test_scenario_record_is_not_gate_evidence(self):
        from omega.records import valid_gates
        self.assertFalse(valid_gates({'kind':'skill-evaluation','passed':True,'results':[]},app.CONFIG['gates']))

    def test_private_parent_symlink_inside_repo_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'safe').mkdir();(root/'safe/file').write_text('content')
            (root/'alias').symlink_to(root/'safe',target_is_directory=True)
            with self.assertRaises(ValueError):packet(root,['alias/file'])

    def test_hook_rejects_missing_cwd_and_policy_test_changes(self):
        from omega.hook import authorize
        self.assertFalse(authorize({'hook_event_name':'PreToolUse','tool_name':'Edit','tool_input':{'file_path':'docs/x'}})[0])
        for path in ('tests/test_omega.py','benchmarks/demo.py','.github/workflows/omega.yml','.gitignore'):
            self.assertFalse(authorize({'hook_event_name':'PreToolUse','cwd':str(app.ROOT),'tool_name':'Write','tool_input':{'file_path':path}})[0])

    def test_hook_background_gate_requires_review(self):
        from omega.hook import authorize
        self.assertFalse(authorize({'hook_event_name':'PreToolUse','cwd':str(app.ROOT),'tool_name':'Bash','tool_input':{'command':'python3 -m omega gates','run_in_background':True}})[0])


class AdapterSafety(unittest.TestCase):
    def test_audit_refuses_symlinked_policy_directory(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'.claude').mkdir();(root/'elsewhere').mkdir()
            (root/'.claude/agents').symlink_to(root/'elsewhere',target_is_directory=True)
            with patch.object(app,'ROOT',root):self.assertFalse(app.audit()['passed'])

    def test_hook_does_not_import_executable_gate_config(self):
        import shutil
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);shutil.copytree(app.ROOT/'omega',root/'omega',ignore=shutil.ignore_patterns('__pycache__'))
            (root/'omega/config.json').write_text('invalid config')
            p=subprocess.run([sys.executable,'-m','omega.hook'],cwd=root,input='{}',text=True,capture_output=True)
            self.assertEqual(p.returncode,2);self.assertNotIn('Traceback',p.stderr)


class CompatibilitySafety(unittest.TestCase):
    def test_local_cli_probe_uses_isolated_state(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);binary=root/'.omega/tools/claude/node_modules/.bin/claude';binary.parent.mkdir(parents=True)
            binary.write_text('#!/bin/sh\nprintf "fixture version\\n"\n');binary.chmod(0o755)
            with patch.object(app,'ROOT',root),patch.object(app.shutil,'which',return_value=None),patch.object(app,'git',side_effect=lambda *a: '' if a[0] in ('ls-files','check-ignore') else 'fixture git'):
                result=app.doctor()
                self.assertTrue(result['claude']['available']);self.assertEqual(result['claude']['source'],'project-local')
                self.assertEqual(result['claude']['exit_code'],0);self.assertTrue((root/'.omega/claude-state').is_dir())

    def test_process_environment_override_does_not_mutate_parent(self):
        import os
        marker='OMEGA_FIXTURE_NON_SECRET'
        self.assertNotIn(marker,os.environ)
        r=execute([sys.executable,'-c','import os;print(os.environ["OMEGA_FIXTURE_NON_SECRET"])'],app.ROOT,env={**os.environ,marker:'isolated'})
        self.assertEqual(r['output'].strip(),'isolated');self.assertNotIn(marker,os.environ)
