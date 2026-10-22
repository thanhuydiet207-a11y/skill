import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import omega.__main__ as app
from omega import change, records


class ProjectFixture(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.root=Path(self.directory.name)
        self.patch=patch.object(app,'ROOT',self.root);self.patch.start()
        (self.root/'.gitignore').write_text('.omega/\n')
        (self.root/'calc.py').write_text('def add(a,b):\n    return a+b\n')
        app.git('init','-q','-b','omega/test')
        app.git('add','.')
        self.commit('initial')

    def tearDown(self):self.patch.stop();self.directory.cleanup()
    def commit(self,message):
        app.git('-c','user.name=OMEGA test','-c','user.email=omega@example.invalid','commit','--allow-empty','-qm',message)
    def plan(self):
        return app.save('changes',change.create(self.root,app.git,['calc.py'],['add(2,3) equals 5'],app.CONFIG['limits']))
    def invoke(self,*args):
        out=io.StringIO()
        with patch.object(sys,'argv',['omega',*args]),contextlib.redirect_stdout(out):code=app.main()
        return code,json.loads(out.getvalue())


class ChangeWorkflow(ProjectFixture):
    def test_scoped_change_and_outside_path_detection(self):
        name=self.plan();(self.root/'calc.py').write_text('fixed')
        self.assertTrue(change.check(self.root,name,app.git,app.CONFIG['limits'])['passed'])
        (self.root/'unrelated.py').write_text('unrelated')
        result=change.check(self.root,name,app.git,app.CONFIG['limits'])
        self.assertFalse(result['passed']);self.assertEqual(result['outside_scope'],['unrelated.py'])

    def test_plan_requires_clean_isolated_checkout(self):
        app.git('switch','-c','main')
        with self.assertRaisesRegex(ValueError,'isolated'):self.plan()
        app.git('switch','omega/test');(self.root/'calc.py').write_text('dirty')
        with self.assertRaisesRegex(ValueError,'clean'):self.plan()

    def test_repair_budget_enforced(self):
        name=self.plan()
        self.assertEqual(change.attempt(self.root,name,'first diagnosis',app.CONFIG['limits'])['remaining'],1)
        self.assertEqual(change.attempt(self.root,name,'second diagnosis',app.CONFIG['limits'])['remaining'],0)
        with self.assertRaisesRegex(ValueError,'exhausted'):change.attempt(self.root,name,'third',app.CONFIG['limits'])

    def test_expired_plan_refuses_repair_and_readiness(self):
        name=self.plan();path=self.root/name;record=json.loads(path.read_text())
        record['opened_at']=time.time()-20;record['deadline']=time.time()-10;path.write_text(json.dumps(record))
        self.assertFalse(change.check(self.root,name,app.git,app.CONFIG['limits'])['passed'])
        with self.assertRaisesRegex(ValueError,'deadline'):change.attempt(self.root,name,'diagnosis',app.CONFIG['limits'])

    def test_branch_or_head_change_is_detected(self):
        name=self.plan();self.commit('different head')
        self.assertFalse(change.check(self.root,name,app.git,app.CONFIG['limits'])['base_head_matches'])
        app.git('switch','-c','omega/other')
        self.assertFalse(change.check(self.root,name,app.git,app.CONFIG['limits'])['branch_matches'])

    def test_gate_record_invalidated_by_source_change(self):
        name=self.plan();state=records.workspace(self.root,app.git)
        ev=app.save('evidence',{'kind':'gates','passed':True,'workspace_unchanged':True,'workspace_sha256':state,'results':[{'gate':k,'command':v,'exit_code':0,'output':'OMEGA_TEST_RESULT {"run": 1, "passed": 1, "failed": 0, "errors": 0, "skipped": 0, "expected_failures": 0, "unexpected_successes": 0}' if k=='tests' else ''} for k,v in app.CONFIG['gates'].items()]})
        self.assertTrue(change.check(self.root,name,app.git,app.CONFIG['limits'],[ev],app.CONFIG['gates'])['passed'])
        (self.root/'calc.py').write_text('changed after evidence')
        self.assertFalse(change.check(self.root,name,app.git,app.CONFIG['limits'],[ev],app.CONFIG['gates'])['passed'])

    def test_rename_checks_old_and_new_paths(self):
        name=self.plan();app.git('mv','calc.py','other.py')
        result=change.check(self.root,name,app.git,app.CONFIG['limits'])
        self.assertIn('other.py',result['outside_scope']);self.assertIn('calc.py',result['changed_paths'])

    def test_gate_failure_if_command_mutates_workspace(self):
        commands={k:[sys.executable,'-c','pass'] for k in app.CONFIG['gates']}
        commands['build']=[sys.executable,'-c','from pathlib import Path;Path("calc.py").write_text("mutated")']
        with patch.object(app,'CONFIG',{**app.CONFIG,'gates':commands}):result=app.gates()
        self.assertFalse(result['passed']);self.assertFalse(result['workspace_unchanged'])
        self.assertTrue(all(row['exit_code']==0 for row in result['results']))


class MemoryWorkflow(ProjectFixture):
    def test_source_and_head_staleness(self):
        code,result=self.invoke('memory','--title','Addition contract','--body','Return sum, evidence reviewed','--select','calc.py')
        self.assertEqual(code,0)
        name=result['memory']
        self.assertFalse(records.memory_status(self.root,name,app.git('rev-parse','HEAD'))['stale'])
        (self.root/'calc.py').write_text('changed')
        self.assertTrue(records.memory_status(self.root,name,app.git('rev-parse','HEAD'))['stale'])
        self.commit('new commit')
        self.assertIn('HEAD changed',records.memory_status(self.root,name,app.git('rev-parse','HEAD'))['reasons'])

    def test_evidence_tamper_and_project_binding(self):
        ev=app.save('evidence',{'passed':True})
        _,out=self.invoke('memory','--title','ADR','--body','Reviewed evidence','--evidence',ev)
        path=self.root/ev;record=json.loads(path.read_text());record['passed']=False;path.write_text(json.dumps(record))
        self.assertTrue(records.memory_status(self.root,out['memory'],app.git('rev-parse','HEAD'))['stale'])
        record['project']='/different/project';path.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError,'project'):records.load(self.root,ev,'evidence')

    def test_missing_evidence_does_not_create_memory(self):
        with self.assertRaises(ValueError):
            self.invoke('memory','--title','ADR','--body','unproven','--evidence','.omega/evidence/missing.json')
        self.assertFalse((self.root/'.omega/memory').exists())

    def test_cli_read_returns_nonzero_for_stale_memory(self):
        _,out=self.invoke('memory','--title','ADR','--body','data only','--select','calc.py')
        (self.root/'calc.py').write_text('changed')
        code,result=self.invoke('memory-read','--record',out['memory'])
        self.assertEqual(code,1);self.assertTrue(result['stale'])


class RepositoryWorkflow(ProjectFixture):
    def test_actual_git_odd_filename_roundtrip(self):
        name=' line\nquote".py';(self.root/name).write_text('pass')
        self.assertIn(name,{row['path'] for row in app.inventory()['files']})

    def test_workspace_hash_tracks_untracked_and_deleted(self):
        before=records.workspace(self.root,app.git)
        (self.root/'new.py').write_text('new')
        self.assertNotEqual(before,records.workspace(self.root,app.git))
        (self.root/'calc.py').unlink()
        self.assertNotEqual(before,records.workspace(self.root,app.git))


class RecordSafety(ProjectFixture):
    def test_duplicate_keys_and_malformed_memory_rejected(self):
        name=app.save('memory',{'kind':'memory','title':'ADR','body':'safe','source_refs':'not a list'})
        with self.assertRaisesRegex(ValueError,'references'):records.memory_status(self.root,name,app.git('rev-parse','HEAD'))
        path=self.root/name
        path.write_text('{"schema":1,"schema":1,"project":'+json.dumps(str(self.root))+'}')
        with self.assertRaisesRegex(ValueError,'Duplicate'):records.load(self.root,name,'memory')

    def test_repair_lock_prevents_concurrent_updates(self):
        import fcntl
        name=self.plan()
        with (self.root/name).open('r+') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaisesRegex(ValueError,'busy'):change.attempt(self.root,name,'diagnosis',app.CONFIG['limits'])
        self.assertEqual(change.attempt(self.root,name,'after release',app.CONFIG['limits'])['remaining'],1)

    def test_scenario_evidence_cannot_replace_gates(self):
        name=self.plan()
        ev=app.save('evidence',{'kind':'skill-evaluation','passed':True,'workspace_unchanged':True,'workspace_sha256':records.workspace(self.root,app.git)})
        self.assertFalse(change.check(self.root,name,app.git,app.CONFIG['limits'],[ev],app.CONFIG['gates'])['passed'])

    def test_worktree_container_itself_refused(self):
        with self.assertRaises(ValueError):self.invoke('isolate','--name','wrong','--worktree','.omega/worktrees')


class ExistingChangeWorkflow(ProjectFixture):
    def test_explicit_existing_changes_preserved_outside_scope(self):
        (self.root/'notes.txt').write_text('User notes')
        plan=change.create(self.root,app.git,['calc.py'],['sum correct'],app.CONFIG['limits'],True)
        record=app.save('changes',plan);(self.root/'calc.py').write_text('updated')
        result=change.check(self.root,record,app.git,app.CONFIG['limits'])
        self.assertTrue(result['scope_passed']);self.assertFalse(result['ready_for_review'])
        (self.root/'notes.txt').write_text('Unexpected edit')
        result=change.check(self.root,record,app.git,app.CONFIG['limits']);self.assertIn('notes.txt',result['outside_scope'])
    def test_index_only_changes_alter_snapshot(self):
        before=records.workspace(self.root,app.git);(self.root/'calc.py').write_text('staged change')
        unstaged=records.workspace(self.root,app.git);app.git('add','calc.py');staged=records.workspace(self.root,app.git)
        self.assertNotEqual(before,unstaged);self.assertNotEqual(unstaged,staged)
