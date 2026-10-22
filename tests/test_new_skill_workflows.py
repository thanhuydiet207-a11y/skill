"""Real CLI scenarios for the eight interoperability extensions, no model calls."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import omega.__main__ as app
from omega.interop import compatibility,handoff,project_adapter
from omega.analysis_tools import interference,context_check,reconcile_evidence,reconcile_memory
from omega.context import packet
from omega.records import workspace,execution_context


class NewSkillWorkflows(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'.gitignore').write_text('.omega/\n')
        (self.root/'app.py').write_text('def answer():\n    return 42\n')
        self.patch=patch.object(app,'ROOT',self.root);self.patch.start()
        self.git('init','-q','-b','omega/fixture');self.git('add','.')
        self.git('-c','user.name=OMEGA fixture','-c','user.email=omega@example.invalid','commit','-qm','fixture')
    def tearDown(self):self.patch.stop();self.temp.cleanup()
    def git(self,*args,raw=False):
        p=subprocess.run(['git',*args],cwd=self.root,text=True,capture_output=True,check=True)
        return p.stdout if raw else p.stdout.strip()
    def document(self,name,value):
        path=self.root/'.omega/inputs'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))
        return str(path.relative_to(self.root))
    def cli(self,*args):
        p=subprocess.run([sys.executable,str(app.ENGINE_ROOT/'omega_cli.py'),'--project-root',str(self.root),*args,'--compact'],cwd=self.root,text=True,capture_output=True)
        return p,json.loads(p.stdout) if p.stdout else None
    def skill(self,directory,name='example',extra=''):
        path=self.root/directory/'SKILL.md';path.parent.mkdir(parents=True)
        path.write_text('---\nname: '+name+'\ndescription: Fixture skill\n'+extra+'---\nRead explicit source only.\n')
        return path.parent

    def test_compatibility_cli_detects_name_collision_without_running_skills(self):
        self.skill('skills/a');self.skill('skills/b')
        p,r=self.cli('skill-compatibility-audit','--skill-root','skills')
        self.assertEqual(p.returncode,1);self.assertIn('same-name-across-roots',{x['kind'] for x in r['findings']})
        self.assertFalse((self.root/'NEVER').exists())
    def test_policy_explainer_cli_identifies_scope_without_granting_platform_access(self):
        event={'hook_event_name':'PreToolUse','cwd':str(self.root),'tool_name':'Bash','tool_input':{'command':'python3 '+str(app.ENGINE_ROOT/'omega_cli.py')+' --project-root '+str(self.root)+' map --compact'}}
        name=self.document('event.json',event);p,r=self.cli('effective-policy-explainer','--input',name)
        self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(r['platform_decision'],'unknown')
        event['tool_input']['command']='git push';name=self.document('event.json',event)
        p,r=self.cli('effective-policy-explainer','--input',name);self.assertEqual(p.returncode,1)
    def test_workflow_cli_checks_ownership_and_order(self):
        doc={'nodes':[{'id':'main','role':'orchestrator','agents':0,'owns':['workflow','git']},
                      {'id':'writer','role':'worker','writes':['app.py'],'after':['main']},
                      {'id':'verify','role':'reviewer','writes':[],'owns':['gates'],'after':['writer']}]}
        name=self.document('plan.json',doc);p,r=self.cli('workflow-handoff-contract','--input',name)
        self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(r['schedule'],[['main'],['writer'],['verify']])
    def test_interference_cli_reports_fixture_regression_and_real_usage_fields(self):
        doc=self.runs();name=self.document('runs.json',doc);p,r=self.cli('skill-interference-benchmark','--input',name)
        self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(r['native_release_eligible']);self.assertEqual(r['arms']['A']['tokens_mean'],100)
        doc['runs'][2]['acceptance']['correct']=False;name=self.document('runs.json',doc)
        p,r=self.cli('skill-interference-benchmark','--input',name);self.assertEqual(p.returncode,1);self.assertEqual(len(r['regressions']),1)
    def test_project_adapter_cli_proposes_without_installing_or_writing_config(self):
        (self.root/'package.json').write_text(json.dumps({'scripts':{'build':'tsc','test':'jest'}}))
        p,r=self.cli('project-workflow-adapter');self.assertEqual(p.returncode,1)
        self.assertEqual(r['proposals'][0]['tests'],['npm','test','--','--json']);self.assertFalse(r['dependencies_installed'])
        self.assertFalse((self.root/'.omega/configs').exists())
    def test_evidence_reconciler_cli_rejects_source_drift(self):
        marker='OMEGA_TEST_RESULT '+json.dumps({'run':1,'passed':1,'failed':0,'errors':0,'skipped':0,'expected_failures':0,'unexpected_successes':0})
        ev=app.save('evidence',{'kind':'gates','passed':True,'workspace_unchanged':True,'execution_fingerprint':execution_context(self.root,app.CONFIG)['sha256'],
            'workspace_sha256':workspace(self.root,self.git),'results':[{'gate':k,'command':v,'exit_code':0,'output':marker if k=='tests' else ''} for k,v in app.CONFIG['gates'].items()]})
        p,r=self.cli('evidence-reconciler','--record',ev);self.assertEqual(p.returncode,0,p.stderr)
        (self.root/'app.py').write_text('changed')
        p,r=self.cli('evidence-reconciler','--record',ev);self.assertEqual(p.returncode,1);self.assertEqual(r['records'][0]['state'],'stale-source')
    def test_memory_reconciliation_cli_preserves_both_conflicting_records(self):
        a=app.save('memory',{'kind':'memory','title':'Database','body':'Choose database A','decision_key':'database'})
        b=app.save('memory',{'kind':'memory','title':'Database','body':'Choose database B','decision_key':'database'})
        name=self.document('memory.json',{'records':[a,b]});p,r=self.cli('memory-reconciliation','--input',name)
        self.assertEqual(p.returncode,1);self.assertEqual(len(r['conflicts']),1);self.assertFalse(r['files_written'])
        self.assertTrue((self.root/a).exists());self.assertTrue((self.root/b).exists())
    def test_context_sufficiency_cli_verifies_content_ranges_and_task_invariants(self):
        requirements={'sources':[{'path':'app.py','start':1,'end':2}],'acceptance':['answer is 42'],'constraints':['Do not install dependencies']}
        p=packet(self.root,['app.py']);p['task']={k:requirements[k] for k in ('acceptance','constraints')}
        name=self.document('context.json',{'requirements':requirements,'packet':p})
        process,result=self.cli('context-sufficiency-check','--input',name);self.assertEqual(process.returncode,0,process.stderr)
        p['sources'][0]['content']='faked';name=self.document('context.json',{'requirements':requirements,'packet':p})
        process,result=self.cli('context-sufficiency-check','--input',name);self.assertEqual(process.returncode,1)
    def runs(self):
        return {'runs':[{'task_id':'task','trial':0,'arm':arm,'model':'fixture','model_version':'1','prompt_sha256':'a'*64,
                         'acceptance':{'correct':True},'tokens':100+i*10,'duration_ms':10,'provenance':'fixture'} for i,arm in enumerate(('A','B','A+B'))]}
