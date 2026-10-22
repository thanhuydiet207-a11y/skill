"""Regression checks for previously accepted false-green evidence and scope gaps."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import omega.__main__ as app
from omega.adapters import outcomes
from omega.interop import handoff
from omega.records import execution_context,current_context,memory_status,valid_gates
from omega.security import audit,python_findings


COUNTS={'run':1,'passed':1,'failed':0,'errors':0,'skipped':0,'expected_failures':0,'unexpected_successes':0}
MARKER='OMEGA_TEST_RESULT '+json.dumps(COUNTS)


class StrictOutcomes(unittest.TestCase):
    def test_root_junit_aggregates_cannot_hide_suite_errors(self):
        for field in ('tests','failures','errors','skipped'):
            text='<testsuites '+field+'="99"><testsuite tests="1"><testcase name="one"/></testsuite></testsuites>'
            self.assertIsNone(outcomes({'exit_code':0,'output':text},'junit'))
    def test_nested_junit_aggregate_and_case_conflicts_rejected(self):
        for text in ('<testsuite tests="1" failures="1"><testcase/></testsuite>',
                     '<testsuites><error/><testcase/></testsuites>',
                     '<testsuite tests="1"><testcase><skipped/><error/></testcase></testsuite>',
                     '<testsuite tests="-1"><testcase/></testsuite>'):
            self.assertIsNone(outcomes({'exit_code':0,'output':text},'junit'))
    def test_consistent_junit_root_and_nested_totals_accepted(self):
        xml='<testsuites tests="2" failures="0" errors="0" skipped="1"><testsuite tests="2" skipped="1"><testcase/><testcase><skipped/></testcase></testsuite></testsuites>'
        self.assertEqual(outcomes({'exit_code':0,'output':xml},'junit')['passed'],1)
    def test_failed_process_flags_override_success_marker(self):
        for flag in ('timed_out','output_limit_exceeded','invalid_utf8'):
            self.assertIsNone(outcomes({'exit_code':0,'output':MARKER,flag:True}))
    def test_marker_must_be_last_and_unique_without_duplicate_keys(self):
        for text in (MARKER+'\nunexpected trailing log',MARKER+'\n'+MARKER,MARKER.replace('"run": 1','"run": 1, "run": 1')):
            self.assertIsNone(outcomes({'exit_code':0,'output':text}))
    def test_go_requires_started_tests_and_final_successful_package(self):
        run={'Action':'run','Package':'p','Test':'T'};passed={'Action':'pass','Package':'p','Test':'T'};package={'Action':'pass','Package':'p'}
        for events in ([run,passed],[passed,package],[run,passed,package,package],[run,passed,package,{'Action':'start','Package':'other'}]):
            self.assertIsNone(outcomes({'exit_code':0,'output':'\n'.join(map(json.dumps,events))},'go'))
        self.assertEqual(outcomes({'exit_code':0,'output':'\n'.join(map(json.dumps,[run,passed,package]))},'go')['passed'],1)
    def test_jest_suite_failure_and_duplicate_json_keys_rejected(self):
        data={'success':True,'numTotalTests':1,'numPassedTests':1,'numFailedTests':0,'numPendingTests':0,'numTodoTests':0}
        for extra in ({'numFailedTestSuites':1},{'testResults':[{'status':'failed'}]}):
            self.assertIsNone(outcomes({'exit_code':0,'output':json.dumps({**data,**extra})},'jest'))
        text=json.dumps(data).replace('"success": true','"success": false, "success": true')
        self.assertIsNone(outcomes({'exit_code':0,'output':text},'jest'))
    def test_timeout_metadata_invalidates_otherwise_successful_gate_record(self):
        commands={name:['reviewed',name] for name in ('build','tests','security','regression')}
        record={'kind':'gates','passed':True,'execution_unchanged':True,'workspace_unchanged':True,
                'results':[{'gate':k,'command':v,'exit_code':0,'output':MARKER if k=='tests' else ''} for k,v in commands.items()]}
        self.assertTrue(valid_gates(record,commands));record['results'][0]['timed_out']=True
        self.assertFalse(valid_gates(record,commands))


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'.gitignore').write_text('.omega/\nignored.lock\n')
        (self.root/'app.py').write_text('answer = 42\n')
        self.git('init','-q','-b','omega/hardening');self.git('add','.')
        self.git('-c','user.name=OMEGA fixture','-c','user.email=omega@example.invalid','commit','-qm','fixture')
        self.scope=patch.object(app,'ROOT',self.root);self.scope.start()
    def tearDown(self):self.scope.stop();self.temp.cleanup()
    def git(self,*args,raw=False):
        p=subprocess.run(['git',*args],cwd=self.root,capture_output=True,text=True,check=True)
        return p.stdout if raw else p.stdout.strip()
    def evidence_memory(self):
        ev=app.save('evidence',{'kind':'gates',**current_context(self.root,self.git,app.CONFIG),
                              'workspace_unchanged':True,'execution_unchanged':True,'passed':False})
        from omega.records import memory_payload
        memory=app.save('memory',memory_payload(self.root,'Decision','Observed test failure',[],[ev]))
        return ev,memory


class MemoryEvidence(Fixture):
    def test_unchanged_evidence_blob_does_not_hide_source_drift(self):
        ev,name=self.evidence_memory();head=self.git('rev-parse','HEAD');before=(self.root/ev).read_bytes()
        self.assertFalse(memory_status(self.root,name,head,current_context(self.root,self.git,app.CONFIG))['requires_validation'])
        (self.root/'app.py').write_text('answer = 0\n')
        result=memory_status(self.root,name,head,current_context(self.root,self.git,app.CONFIG))
        self.assertTrue(result['stale']);self.assertEqual(result['evidence_checks'][0]['state'],'stale-context')
        self.assertEqual((self.root/ev).read_bytes(),before)
    def test_unbound_evidence_requires_review(self):
        from omega.records import memory_payload
        ev=app.save('evidence',{'passed':True});name=app.save('memory',memory_payload(self.root,'ADR','Unproven fact',[],[ev]))
        result=memory_status(self.root,name,self.git('rev-parse','HEAD'),current_context(self.root,self.git,app.CONFIG))
        self.assertTrue(result['requires_validation']);self.assertEqual(result['evidence_checks'][0]['state'],'unbound')
    def test_library_without_runtime_context_does_not_claim_evidence_current(self):
        _,name=self.evidence_memory();result=memory_status(self.root,name,self.git('rev-parse','HEAD'))
        self.assertTrue(result['requires_validation']);self.assertEqual(result['evidence_checks'][0]['state'],'not-checked')
    def test_memory_context_detects_environment_change(self):
        _,name=self.evidence_memory()
        with patch.dict(os.environ,{'NODE_OPTIONS':'opaque private fixture'}):
            from omega.records import current_context
            result=memory_status(self.root,name,self.git('rev-parse','HEAD'),current_context(self.root,self.git,app.CONFIG))
        self.assertTrue(result['stale']);self.assertEqual(result['evidence_checks'][0]['state'],'stale-context')


class RuntimeBinding(Fixture):
    def test_external_project_context_is_bound_to_engine_implementation(self):
        from omega.records import engine_digest
        engine=self.root/'trusted-engine';(engine/'omega').mkdir(parents=True)
        source=engine/'omega/runner.py';source.write_text('version = 1')
        before=engine_digest(engine);source.write_text('version = 2');after=engine_digest(engine)
        self.assertNotEqual(before,after)
        with patch('omega.records.engine_digest',return_value=before):first=execution_context(self.root,app.CONFIG)
        with patch('omega.records.engine_digest',return_value=after):second=execution_context(self.root,app.CONFIG)
        self.assertNotEqual(first['sha256'],second['sha256'])
    def test_environment_fingerprint_changes_without_exposing_value(self):
        before=execution_context(self.root,app.CONFIG)['sha256'];private='private fixture value never to print'
        with patch.dict(os.environ,{'NODE_OPTIONS':private}):after=execution_context(self.root,app.CONFIG)
        self.assertNotEqual(before,after['sha256']);self.assertNotIn(private,json.dumps(after))
    def test_declared_ignored_dependency_file_changes_runtime_fingerprint(self):
        file=self.root/'ignored.lock';file.write_text('dependency version one');config={**app.CONFIG,'runtime_inputs':['ignored.lock']}
        before=execution_context(self.root,config)['sha256'];file.write_text('dependency version two')
        self.assertNotEqual(before,execution_context(self.root,config)['sha256'])
    def test_missing_private_or_symlink_input_refused_before_any_gate(self):
        (self.root/'.env').write_text('do not read');(self.root/'alias').symlink_to(self.root/'app.py')
        for name in ('missing.lock','.env','alias'):
            with patch.object(app,'CONFIG',{**app.CONFIG,'runtime_inputs':[name]}),patch.object(app,'run') as run,patch('omega.records.workspace',return_value='snapshot'):
                with self.assertRaises(ValueError):app.gates()
                run.assert_not_called()
    def test_oversized_runtime_input_is_not_hashed(self):
        (self.root/'ignored.lock').write_bytes(b'x'*1048577)
        with self.assertRaises(ValueError):execution_context(self.root,{**app.CONFIG,'runtime_inputs':['ignored.lock']})
    def test_locked_ledger_is_revalidated_after_initial_read(self):
        import omega.change as change
        from omega.records import load
        name=app.save('changes',change.create(self.root,self.git,['app.py'],['answer is 42'],app.CONFIG['limits']))
        def replace_after_initial_load(*args):
            path,record=load(*args);path.write_text('{"schema":1,"schema":1}');return path,record
        with patch('omega.change.load',side_effect=replace_after_initial_load):
            with self.assertRaisesRegex(ValueError,'Duplicate'):change.attempt(self.root,name,'Recheck source',app.CONFIG['limits'])


class ScopeContracts(unittest.TestCase):
    def workflow(self):return {'nodes':[{'id':'main','role':'orchestrator','agents':0},
        {'id':'writer','role':'worker','after':['main'],'writes':['src/app.py']},
        {'id':'reader','role':'reviewer','after':['main'],'reads':['src/app.py']}]}
    def test_unordered_reader_writer_rejected_with_no_actionable_schedule(self):
        with tempfile.TemporaryDirectory() as d:
            result=handoff(d,self.workflow());self.assertFalse(result['passed']);self.assertEqual(result['schedule'],[])
            self.assertTrue(any('reader/writer' in x for x in result['issues']))
    def test_directory_writer_conflicts_with_descendant_but_not_similar_prefix(self):
        with tempfile.TemporaryDirectory() as d:
            doc=self.workflow();doc['nodes'][1].update(writes=[],write_dirs=['src']);doc['nodes'][2].update(reads=['src/app.py'])
            self.assertFalse(handoff(d,doc)['passed']);doc['nodes'][2]['reads']=['src-other/app.py']
            self.assertTrue(handoff(d,doc)['passed'])
    def test_ordered_reader_writer_and_directory_writer_pass(self):
        with tempfile.TemporaryDirectory() as d:
            doc=self.workflow();doc['nodes'][1].update(writes=[],write_dirs=['src']);doc['nodes'][2]['after']=['writer']
            self.assertTrue(handoff(d,doc)['passed'])
    def test_worker_cannot_run_before_orchestrator(self):
        with tempfile.TemporaryDirectory() as d:
            doc=self.workflow();doc['nodes'][1]['after']=[]
            self.assertFalse(handoff(d,doc)['passed'])
    def test_misspelled_or_glob_scopes_require_review(self):
        with tempfile.TemporaryDirectory() as d:
            for extra in ({'write_directory':['src']},{'writes':['src/*.py']}):
                doc=self.workflow();doc['nodes'][1].update(extra)
                with self.assertRaises(ValueError):handoff(d,doc)


class SecurityRules(unittest.TestCase):
    def test_aliased_and_dynamic_subprocess_shell_rules(self):
        for text in ('from subprocess import run as r\nr(["echo"], shell=True)','import subprocess as p\np.run(argv, shell=option)','import subprocess\nsubprocess.run(argv, **options)'):
            self.assertTrue(python_findings(text))
    def test_reviewed_argv_without_shell_does_not_trigger(self):
        self.assertFalse(python_findings('import subprocess\nsubprocess.run(["echo", "literal"], shell=False)'))
    def test_dynamic_execution_and_unsafe_deserialization_rules(self):
        for text in ('eval(payload)','exec(payload)','import pickle as p\np.loads(payload)','import yaml\nyaml.load(payload)'):
            self.assertTrue(python_findings(text))
        self.assertFalse(python_findings('import yaml\nyaml.load(payload, Loader=yaml.SafeLoader)'))
    def test_tls_disabled_rules(self):
        for text in ('import ssl\nssl._create_unverified_context()','import requests as r\nr.get(url, verify=False)'):
            self.assertTrue(python_findings(text))
    def test_secret_findings_never_echo_source_value(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);private='gh'+'p_'+'A'*30;(root/'config.txt').write_text('value='+private)
            result=audit(root,['config.txt']);self.assertFalse(result['passed']);self.assertNotIn(private,json.dumps(result))
            self.assertEqual(result['findings'][0]['line'],1)
    def test_scanner_does_not_execute_embedded_code_or_modify_source(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);file=root/'bad.py';file.write_text('import os\nos.system("touch NEVER")\n');before=file.read_bytes()
            result=audit(root,['bad.py']);self.assertFalse(result['passed']);self.assertFalse((root/'NEVER').exists());self.assertEqual(file.read_bytes(),before)
    def test_symlink_binary_missing_and_large_files_are_incomplete(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'binary').write_bytes(b'\0');(root/'alias').symlink_to(root/'binary');(root/'large').write_bytes(b'x'*1048577)
            for path in ('binary','alias','missing','large'):
                self.assertFalse(audit(root,[path])['complete_for_selected_paths'])
    def test_default_policy_scan_still_rejects_disabled_hooks_and_invalid_json(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'.claude').mkdir();file=root/'.claude/settings.json'
            for text in ('{"disableAllHooks":true}','{"a":1,"a":2}','{"permissions":{"defaultMode":"bypass\\u0050ermissions"}}'):
                file.write_text(text);self.assertFalse(audit(root)['passed'])
    def test_generated_bytecode_exclusion_is_reported_without_deleting_files(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);file=root/'src/__pycache__/generated.pyc';file.parent.mkdir(parents=True);file.write_bytes(b'\0binary')
            (root/'src/safe.py').write_text('answer=42')
            result=audit(root,['src']);self.assertTrue(result['passed']);self.assertTrue(result['exclusions']);self.assertTrue(file.exists())
            self.assertFalse(audit(root,['src/__pycache__/generated.pyc'])['passed'])
