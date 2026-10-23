import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import omega.__main__ as app
from omega.skills import assess, HEADINGS, suite_digest


class SkillEvolution(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        from tests.skill_fixture import write_skill
        self.old=write_skill(self.root)
        self.stable=self.root/'.claude/skills/omega/SKILL.md'

    def tearDown(self):self.temp.cleanup()
    def candidate(self,text):
        path=self.root/'.omega/candidates/test.md';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        return str(path.relative_to(self.root))
    def advanced(self):return self.old+'\n'+'\n'.join('## '+x+'\nExplicit evidence and limits.' for x in HEADINGS)
    def invoke(self,*args):
        out=io.StringIO()
        with patch.object(sys,'argv',['omega',*args]),contextlib.redirect_stdout(out):code=app.main()
        return code,json.loads(out.getvalue())
    def baseline(self):
        return self.invoke('candidate','--skill','omega')[1]
    def report(self):return {'suite':'fixture','suite_sha256':'stable-suite','cases':[{'id':'one','passed':True}],'passed':True}

    def test_legacy_contract_is_valid_but_needs_advanced_sections(self):
        result=assess(self.root,'omega')
        self.assertTrue(result['passed']);self.assertFalse(result['advanced_passed'])
        new=assess(self.root,'omega',self.candidate(self.advanced()))
        self.assertTrue(new['advanced_passed']);self.assertGreater(new['score'],result['score'])

    def test_bypass_wrong_identity_and_missing_command_rejected(self):
        for text in (self.advanced()+'\n--dangerously-skip-permissions',self.advanced().replace('name: omega','name: other'),self.advanced().replace('python3 -m omega map','missing command')):
            self.assertFalse(assess(self.root,'omega',self.candidate(text))['passed'])

    def test_duplicate_or_unknown_frontmatter_refused(self):
        for field in ('name: omega','permissionMode: bypassPermissions'):
            text=self.advanced().replace('description: Fixture','description: Fixture\n'+field)
            self.assertFalse(assess(self.root,'omega',self.candidate(text))['passed'])

    def test_oversized_skill_and_candidate_namespace(self):
        with self.assertRaises(ValueError):assess(self.root,'omega',self.candidate('x'*8193))
        with self.assertRaises(ValueError):assess(self.root,'omega','README.md')

    def test_benchmark_hash_tracks_execution_code(self):
        h=suite_digest(self.root)
        p=self.root/'omega';p.mkdir();(p/'process.py').write_text('new runner')
        self.assertNotEqual(h,suite_digest(self.root))
        h=suite_digest(self.root);(self.root/'tests').mkdir()
        (self.root/'tests/test_new.py').write_text('new regression')
        self.assertNotEqual(h,suite_digest(self.root))
        h=suite_digest(self.root);(self.root/'integration/typescript').mkdir(parents=True)
        (self.root/'integration/typescript/bridge.ts').write_text('export type Task = string;')
        self.assertNotEqual(h,suite_digest(self.root))

    def test_missing_sections_cannot_pass_comparison(self):
        with patch.object(app,'ROOT',self.root),patch.object(app,'git',side_effect=lambda *a: '' if a[0] in ('ls-files','check-ignore') else 'abc'),patch.object(app,'benchmark',return_value=self.report()):
            b=self.baseline()
            code,result=self.invoke('compare','--baseline',b['baseline'])
            self.assertEqual(code,1);self.assertFalse(result['eligible_for_review'])

    def test_no_evidence_is_not_eligible_for_review(self):
        with patch.object(app,'ROOT',self.root),patch.object(app,'git',side_effect=lambda *a: '' if a[0] in ('ls-files','check-ignore') else 'abc'),patch.object(app,'benchmark',return_value=self.report()):
            b=self.baseline();(self.root/b['candidate']).write_text(self.advanced())
            code,result=self.invoke('compare','--baseline',b['baseline'])
            self.assertEqual(code,0);self.assertFalse(result['eligible_for_review'])

    def test_current_gate_and_scenario_evidence_required(self):
        with patch.object(app,'ROOT',self.root),patch.object(app,'git',side_effect=lambda *a: '' if a[0] in ('ls-files','check-ignore') else 'abc'),patch.object(app,'benchmark',return_value=self.report()),patch('omega.records.workspace',return_value='current-workspace'):
            b=self.baseline();(self.root/b['candidate']).write_text(self.advanced())
            assessment=assess(self.root,'omega',b['candidate'])
            from omega.records import execution_context
            common={'execution_fingerprint':execution_context(self.root,app.CONFIG)['sha256'],'execution_unchanged':True,'kind':'gates','passed':True,'workspace_sha256':'current-workspace','workspace_unchanged':True}
            gate=app.save('evidence',{**common,'results':[{'gate':name,'command':app.CONFIG['gates'][name],'exit_code':0,'output':'OMEGA_TEST_RESULT {"run": 1, "passed": 1, "failed": 0, "errors": 0, "skipped": 0, "expected_failures": 0, "unexpected_successes": 0}' if name=='tests' else ''} for name in app.CONFIG['gates']]})
            scenario=app.save('evidence',{**common,'kind':'skill-evaluation','skill':'omega','candidate_sha256':assessment['sha256'],'candidate_bundle_sha256':assessment['bundle_sha256'],'suite_sha256':'stable-suite','scenarios':{'exit_code':0,'output':'OMEGA_TEST_RESULT {"run": 1, "passed": 1, "failed": 0, "errors": 0, "skipped": 0, "expected_failures": 0, "unexpected_successes": 0}'}})
            code,result=self.invoke('compare','--baseline',b['baseline'],'--evidence',gate,'--evidence',scenario)
            self.assertEqual(code,0);self.assertTrue(result['eligible_for_review'])
            (self.root/b['candidate']).write_text(self.advanced()+'\nchanged after scenario')
            code,result=self.invoke('compare','--baseline',b['baseline'],'--evidence',gate,'--evidence',scenario)
            self.assertEqual(code,1);self.assertFalse(result['eligible_for_review'])

    def test_stale_gate_evidence_refused(self):
        with patch.object(app,'ROOT',self.root),patch.object(app,'git',side_effect=lambda *a: '' if a[0] in ('ls-files','check-ignore') else 'abc'),patch.object(app,'benchmark',return_value=self.report()),patch('omega.records.workspace',return_value='new-workspace'):
            b=self.baseline();(self.root/b['candidate']).write_text(self.advanced())
            ev=app.save('evidence',{'passed':True,'workspace_sha256':'old-workspace','workspace_unchanged':True,'results':[{'gate':name,'command':app.CONFIG['gates'][name],'exit_code':0,'output':'OMEGA_TEST_RESULT {"run": 1, "passed": 1, "failed": 0, "errors": 0, "skipped": 0, "expected_failures": 0, "unexpected_successes": 0}' if name=='tests' else ''} for name in app.CONFIG['gates']]})
            code,result=self.invoke('compare','--baseline',b['baseline'],'--evidence',ev)
            self.assertEqual(code,1);self.assertFalse(result['eligible_for_review'])
