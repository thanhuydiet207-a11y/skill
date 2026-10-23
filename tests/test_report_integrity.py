"""Report lifecycle and process regressions; synthetic reports are not framework runs."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import omega.__main__ as app
from omega.context import gate_summary
from omega.records import test_outcomes,valid_gates,engine_digest
from omega.skills import suite_digest
from omega.adapters import outcomes


REPORTER='''import json,os,sys
from pathlib import Path
p=Path(sys.argv[1]);mode=sys.argv[2]
xml='<testsuite tests="1" failures="0" errors="0" skipped="0"><testcase name="fixture"/></testsuite>'
data={'success':True,'numTotalTests':1,'numPassedTests':1,'numFailedTests':0,'numPendingTests':0,'numTodoTests':0}
if mode=='missing':pass
elif mode=='symlink':p.symlink_to(Path('old.xml').resolve())
elif mode=='hardlink':os.link('old.xml',p)
elif mode=='fifo':os.mkfifo(p)
elif mode=='large':p.write_bytes(b'x'*262145)
elif mode=='bad-utf8':p.write_bytes(b'\\xff')
elif mode=='bad-encoding-budget':p.write_bytes(b'\\x01'*262144)
elif mode=='failed':p.write_text(xml.replace('<testcase name="fixture"/>','<testcase><failure/></testcase>').replace('failures="0"','failures="1"'));sys.exit(1)
else:p.write_text(json.dumps(data) if mode=='jest' else xml)
print('human runner logs, not structured report output')
if mode=='noisy':sys.stdout.write('á'*20001)
'''


class ReportLifecycle(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'.gitignore').write_text('.omega/\n__pycache__/\n')
        (self.root/'reporter.py').write_text(REPORTER)
        (self.root/'old.xml').write_text('<testsuite tests="1"><testcase/></testsuite>')
        self.git('init','-q','-b','omega/report-fixture');self.git('add','.')
        self.git('-c','user.name=OMEGA fixture','-c','user.email=omega@example.invalid','commit','-qm','report fixture')
        self.scope=patch.object(app,'ROOT',self.root);self.scope.start()
    def tearDown(self):self.scope.stop();self.temp.cleanup()
    def git(self,*args):return subprocess.check_output(['git',*args],cwd=self.root,text=True).strip()
    def config(self,mode='valid',adapter='junit'):
        commands={key:[sys.executable,'-c','pass'] for key in ('build','tests','security','regression')}
        commands['tests']=[sys.executable,'reporter.py','{report_path}',mode]
        return {**app.CONFIG,'gates':commands,'test_adapter':adapter,'test_report':'.omega/reports/{run_id}/tests.xml'}
    def gates(self,mode='valid',adapter='junit',config=None):
        with patch.object(app,'CONFIG',config or self.config(mode,adapter)):return app.gates()
    def test_noisy_junit_report_is_separate_from_logs(self):
        result=self.gates('noisy');self.assertTrue(result['passed']);row=result['results'][1]
        self.assertTrue(row['truncated']);self.assertFalse(row['invalid_utf8']);self.assertEqual(result['test_outcomes']['passed'],1)
        self.assertTrue(row['report']['fresh']);self.assertTrue(row['report']['unchanged'])
    def test_jest_file_counts_do_not_parse_mixed_stdout(self):
        result=self.gates('jest','jest');self.assertTrue(result['passed']);self.assertIn('human runner logs',result['results'][1]['output'])
        self.assertEqual(result['test_outcomes']['passed'],1)
    def test_missing_report_does_not_reuse_old_file(self):
        before=(self.root/'old.xml').read_bytes();result=self.gates('missing')
        self.assertFalse(result['passed']);self.assertIsNone(result['test_outcomes']);self.assertEqual((self.root/'old.xml').read_bytes(),before)
    def test_every_run_uses_a_new_report_namespace_without_deleting_history(self):
        first=self.gates();second=self.gates()
        a=first['results'][1]['report']['path'];b=second['results'][1]['report']['path']
        self.assertNotEqual(a,b);self.assertTrue((self.root/a).is_file());self.assertTrue((self.root/b).is_file())
    def test_failed_test_cannot_be_overridden_by_report_presence(self):
        result=self.gates('failed');self.assertFalse(result['passed']);self.assertIsNone(result['test_outcomes'])
    def test_symlink_hardlink_and_fifo_reports_fail_without_blocking(self):
        for mode in ('symlink','hardlink','fifo'):
            with self.subTest(mode=mode):
                result=self.gates(mode);self.assertFalse(result['passed']);self.assertIsNone(result['test_outcomes'])
    def test_oversized_invalid_utf8_and_unsafe_encoding_reports_fail(self):
        for mode in ('large','bad-utf8','bad-encoding-budget'):
            with self.subTest(mode=mode):self.assertFalse(self.gates(mode)['passed'])
    def test_report_modified_by_later_gate_is_not_ready(self):
        config=self.config();config['gates']['regression']=[sys.executable,'-c','from pathlib import Path;next(Path(".omega/reports").glob("*/tests.xml")).write_text("changed after tests")']
        result=self.gates(config=config);self.assertFalse(result['passed']);self.assertFalse(result['results'][1]['report']['unchanged'])
    def test_gate_record_binds_template_actual_argv_and_report_content(self):
        config=self.config();result=self.gates(config=config);record=json.loads((self.root/app.save('evidence',result)).read_text())
        self.assertTrue(valid_gates(record,config['gates'],'junit',config['test_report']))
        self.assertFalse(valid_gates(record,config['gates'],'junit'))
        row=record['results'][1];original=list(row['command']);row['command'][-1]='different'
        self.assertFalse(valid_gates(record,config['gates'],'junit',config['test_report']));row['command']=original
        row['report']['content']+=' '
        self.assertIsNone(test_outcomes(row));self.assertFalse(valid_gates(record,config['gates'],'junit',config['test_report']))
    def test_summary_references_report_without_mutating_full_evidence(self):
        result=self.gates();result['evidence']=app.save('evidence',result);original=result['results'][1]['report']['content']
        summary=gate_summary(result);report=summary['results'][1]['report']
        self.assertNotIn('content',report);self.assertIn('/report/content',report['content_ref'])
        self.assertEqual(result['results'][1]['report']['content'],original)
        restored=json.loads((self.root/result['evidence']).read_text())['results'][1]['report']['content'];self.assertEqual(restored,original)
    def test_report_directory_symlink_is_refused_before_commands(self):
        (self.root/'.omega').mkdir();(self.root/'.omega/reports').symlink_to(self.root,target_is_directory=True)
        with patch.object(app,'CONFIG',self.config()),patch.object(app,'run') as run,patch('omega.records.workspace',return_value='state'),patch.object(app,'runtime_ready'):
            with self.assertRaises(ValueError):app.gates()
            run.assert_not_called()
    def test_invalid_policies_are_rejected_before_any_command(self):
        variants=[{**self.config(),'test_report':'../outside.xml'},{**self.config(),'test_report':'.omega/reports/reused.xml'},
                  {**self.config(),'test_adapter':'omega'}, {**self.config(),'test_report':None}]
        bad=self.config();bad['gates']['tests'][0]='{report_path}';variants.append(bad)
        bad=self.config();bad['gates']['build']=[sys.executable,'{report_path}'];variants.append(bad)
        for config in variants:
            with patch.object(app,'CONFIG',config),patch.object(app,'run') as run:
                with self.assertRaises(ValueError):app.gates()
                run.assert_not_called()


class OutputAndSourceIntegrity(unittest.TestCase):
    def test_jest_case_details_and_interruption_cannot_contradict_totals(self):
        data={'success':True,'numTotalTests':1,'numPassedTests':1,'numFailedTests':0,'numPendingTests':0,'numTodoTests':0}
        for extra in ({'wasInterrupted':True},{'numRuntimeErrorTestSuites':1},{'testResults':[]},
                      {'testResults':[{'status':'passed','assertionResults':[{'status':'failed'}]}]}):
            self.assertIsNone(outcomes({'exit_code':0,'output':json.dumps({**data,**extra})},'jest'))
        data['testResults']=[{'status':'passed','assertionResults':[{'status':'passed'}]}]
        self.assertEqual(outcomes({'exit_code':0,'output':json.dumps(data)},'jest')['passed'],1)
    def test_go_event_order_and_junit_case_containers_are_validated(self):
        run={'Action':'run','Package':'p','Test':'T'};passed={**run,'Action':'pass'};package={'Action':'pass','Package':'p'}
        for events in ([passed,run,package],[package,run,passed]):
            self.assertIsNone(outcomes({'exit_code':0,'output':'\n'.join(map(json.dumps,events))},'go'))
        self.assertIsNone(outcomes({'exit_code':0,'output':'<testsuites><system-out><testcase/></system-out></testsuites>'},'junit'))
    def test_valid_utf8_split_capture_boundary_is_not_corrupt_process_output(self):
        from omega.process import execute
        result=execute([sys.executable,'-c','import sys;sys.stdout.write("á"*200)'],app.ENGINE_ROOT,capture_bytes=3)
        self.assertTrue(result['truncated']);self.assertFalse(result['invalid_utf8'])
    def test_actually_invalid_utf8_is_detected_even_outside_prefix(self):
        from omega.process import execute
        result=execute([sys.executable,'-c','import os;os.write(1,b"a"*500+b"\\xff")'],app.ENGINE_ROOT,capture_bytes=10)
        self.assertTrue(result['invalid_utf8'])
    def test_dependency_sources_are_pruned_but_lock_changes_invalidate_suite(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);dep=root/'integration/typescript/node_modules/pkg/source.ts';dep.parent.mkdir(parents=True);dep.write_text('dependency one')
            lock=root/'integration/typescript/package-lock.json';lock.write_text('{"version":1}')
            before=suite_digest(root);dep.write_text('dependency two');self.assertEqual(before,suite_digest(root))
            lock.write_text('{"version":2}');self.assertNotEqual(before,suite_digest(root))
    def test_engine_source_symlink_directory_is_not_silently_omitted(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'omega').mkdir();(root/'outside').mkdir();(root/'omega/alias').symlink_to(root/'outside',target_is_directory=True)
            with self.assertRaises(ValueError):engine_digest(root)
            with self.assertRaises(ValueError):suite_digest(root)
