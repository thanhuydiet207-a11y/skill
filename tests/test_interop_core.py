import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import omega.__main__ as app
from omega.adapters import outcomes
from omega.policy import explain
from omega.records import workspace


class PolicyContracts(unittest.TestCase):
    def event(self,command):return {'hook_event_name':'PreToolUse','cwd':str(app.ENGINE_ROOT),'tool_name':'Bash','tool_input':{'command':command}}
    def test_recommended_command_variants_allowed(self):
        for command in ('python3 -m omega gates --summary --compact','python3 -m omega doctor --compact','python3 -m omega map --compact','python3 -m omega context --select omega/context.py:1:5 --compact','python3 -m omega change-plan --allow app.py --acceptance "returns expected value" --compact'):
            self.assertTrue(explain(self.event(command))['allowed'],command)
    def test_composition_substitution_and_unknown_arguments_refused(self):
        for command in ('python3 -m omega gates; git push','python3 -m omega gates $(id)','python3 -m omega gates `id`','python3 -m omega gates > out','python3 -m omega gates --unknown','python3 -c "print(1)"','python3 -m omega gates\necho unsafe'):
            self.assertFalse(explain(self.event(command))['allowed'],command)
    def test_explanation_never_claims_platform_permission(self):
        result=explain(self.event('python3 -m omega gates'))
        self.assertEqual(result['platform_decision'],'unknown');self.assertTrue(result['allowed'])
    def test_hook_and_cli_grammar_agree_on_invalid_summary(self):
        self.assertFalse(explain(self.event('python3 -m omega map --summary'))['allowed'])


class OutcomeAdapters(unittest.TestCase):
    def result(self,text,**kwargs):return {'exit_code':0,'output':text,'truncated':False,**kwargs}
    def test_jest_counts(self):
        data={'success':True,'numTotalTests':3,'numPassedTests':2,'numFailedTests':0,'numPendingTests':1,'numTodoTests':0}
        self.assertEqual(outcomes(self.result(json.dumps(data)),'jest')['skipped'],1)
        data['numTotalTests']=4;self.assertIsNone(outcomes(self.result(json.dumps(data)),'jest'))
    def test_jest_zero_tests_and_boolean_counts_rejected(self):
        data={'success':True,'numTotalTests':0,'numPassedTests':0,'numFailedTests':0,'numPendingTests':0,'numTodoTests':0}
        self.assertIsNone(outcomes(self.result(json.dumps(data)),'jest'))
        data.update(numTotalTests=1,numPassedTests=True)
        self.assertIsNone(outcomes(self.result(json.dumps(data)),'jest'))
    def test_go_events_not_package_pass(self):
        package='example.test/app'
        events=[{'Package':package,'Action':'run','Test':'TestSum'},{'Package':package,'Action':'pass','Test':'TestSum'},{'Package':package,'Action':'pass'}]
        result=outcomes(self.result('\n'.join(map(json.dumps,events))),'go')
        self.assertEqual(result['passed'],1)
        self.assertIsNone(outcomes(self.result(json.dumps({'Package':package,'Action':'pass'})),'go'))
    def test_go_missing_terminal_duplicate_and_package_failure(self):
        events=[{'Package':'p','Action':'run','Test':'T'}]
        self.assertIsNone(outcomes(self.result(json.dumps(events[0])),'go'))
        events+=[{'Package':'p','Action':'pass','Test':'T'},{'Package':'p','Action':'pass','Test':'T'}]
        self.assertIsNone(outcomes(self.result('\n'.join(map(json.dumps,events))),'go'))
        self.assertIsNone(outcomes(self.result('{"Package":"p","Action":"fail"}'),'go'))
    def test_junit_actual_cases_and_invalid_totals(self):
        xml='<testsuite tests="2"><testcase name="pass"/><testcase name="skip"><skipped/></testcase></testsuite>'
        self.assertEqual(outcomes(self.result(xml),'junit')['run'],2)
        self.assertIsNone(outcomes(self.result(xml.replace('tests="2"','tests="99"')),'junit'))
    def test_junit_entity_and_failed_case_rejected(self):
        for text in ('<!DOCTYPE x [<!ENTITY x SYSTEM "file:///etc/passwd">]><testsuite/>','<testsuite><testcase><failure/></testcase></testsuite>'):
            self.assertIsNone(outcomes(self.result(text),'junit'))
    def test_truncated_structured_formats_not_accepted(self):
        for adapter in ('jest','go','junit'):
            self.assertIsNone(outcomes(self.result('{}',truncated=True),adapter))


class PortableEngine(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'.gitignore').write_text('.omega/\n__pycache__/\n')
        (self.root/'app.py').write_text('def answer(): return 42\n')
        (self.root/'checks').mkdir();(self.root/'checks/test_app.py').write_text('import unittest\nfrom app import answer\nclass T(unittest.TestCase):\n def test_answer(self):self.assertEqual(answer(),42)\n')
        self.git('init','-q');self.git('add','.')
        self.git('-c','user.name=OMEGA fixture','-c','user.email=omega@example.invalid','commit','-qm','fixture')
    def tearDown(self):self.temp.cleanup()
    def git(self,*args,raw=False):
        r=subprocess.run(['git',*args],cwd=self.root,text=True,capture_output=True,check=True)
        return r.stdout if raw else r.stdout.strip()
    def cli(self,*args):return subprocess.run([sys.executable,str(app.ENGINE_ROOT/'omega_cli.py'),'--project-root',str(self.root),*args],cwd=self.root,text=True,capture_output=True)
    def test_portable_map_targets_host_not_engine(self):
        p=self.cli('map','--compact');self.assertEqual(p.returncode,0,p.stderr)
        paths={r['path'] for r in json.loads(p.stdout)['files']};self.assertIn('app.py',paths);self.assertNotIn('omega/__main__.py',paths)
    def test_external_gates_require_explicit_policy(self):
        p=self.cli('gates');self.assertEqual(p.returncode,2);self.assertIn('explicit reviewed',p.stderr)
    def test_absolute_runner_does_not_import_host_omega_module(self):
        (self.root/'omega.py').write_text('raise RuntimeError("wrong engine")')
        p=self.cli('map','--compact');self.assertEqual(p.returncode,0,p.stderr)
    def test_reviewed_external_gates_run_actual_target_tests(self):
        directory=self.root/'.omega/configs';directory.mkdir(parents=True)
        test=[sys.executable,str(app.ENGINE_ROOT/'omega/test_runner.py'),'--start','checks']
        compile_=[sys.executable,'-m','compileall','-q','app.py']
        config={'schema':1,'gates':{'build':compile_,'tests':test,'security':compile_,'regression':test},'test_adapter':'omega'}
        (directory/'gates.json').write_text(json.dumps(config))
        p=self.cli('gates','--gate-config','.omega/configs/gates.json','--compact');self.assertEqual(p.returncode,0,p.stderr+p.stdout)
        data=json.loads(p.stdout);self.assertEqual(data['test_outcomes']['passed'],1)
        evidence=json.loads((self.root/data['evidence']).read_text());self.assertEqual(evidence['project'],str(self.root))
    def test_mode_change_invalidates_workspace(self):
        path=self.root/'app.py';path.chmod(0o644);before=workspace(self.root,self.git);path.chmod(0o755)
        self.assertNotEqual(before,workspace(self.root,self.git))
    def test_doctor_reports_unknown_external_state(self):
        with patch.object(app.shutil,'which',return_value=None):
            data=app.doctor();self.assertEqual(data['hooks_enabled'],'unknown');self.assertEqual(data['mcp_enabled'],'unknown')
