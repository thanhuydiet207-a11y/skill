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
