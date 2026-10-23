import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import omega.__main__ as app
from omega.hook import authorize


class OmegaTests(unittest.TestCase):
    def test_catalog_foundation_and_eight_extensions(self):
        catalog=json.loads((app.ROOT/'omega/catalog.json').read_text())
        self.assertEqual(len(catalog),44)
        self.assertEqual(sum(x.get("origin")=="foundation" for x in catalog),36)
        self.assertEqual(len({x['name'] for x in catalog}),44)
        self.assertEqual(sum(x['state']=='implemented' for x in catalog),13)
        self.assertEqual(len({x['group'] for x in catalog}),6)
        from omega.skills import MODES
        self.assertEqual(set(MODES),{x['name'] for x in catalog if x['state']=='implemented'})
        self.assertEqual([p.parent.name for p in (app.ROOT/'.claude/skills').glob('*/SKILL.md')],['omega'])

    def test_router_contract(self):self.assertTrue(app.benchmark()['passed'])
    def test_router_complexity(self):
        self.assertEqual(app.plan('high',True)['isolation'],'worktree')
        self.assertEqual(app.plan('low')['agents'],[])
        self.assertEqual(app.plan('high')['max_concurrent_agents'],2)

    def test_path_escape(self):
        for name in ('../outside','/tmp/outside','.'):
            with self.assertRaises(ValueError):app.confined(name)

    def test_symlink_escape(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'escape').symlink_to('/tmp')
            with patch.object(app,'ROOT',root):
                with self.assertRaises(ValueError):app.confined('escape/file')

    def test_subprocess_failure(self):
        result=app.run([sys.executable,'-c','import sys; print("failure evidence"); sys.exit(7)'])
        self.assertEqual(result['exit_code'],7)
        self.assertIn('failure evidence',result['output'])

    def test_timeout(self):
        result=app.run([sys.executable,'-c','import time; time.sleep(10)'],0.05)
        self.assertEqual(result['exit_code'],124)

    def test_no_shell_expansion(self):
        result=app.run([sys.executable,'-c','import sys;print(sys.argv[1])','$(touch NEVER); echo unsafe'])
        self.assertIn('$(touch NEVER)',result['output'])

    def test_gate_failure_propagates(self):
        with patch.object(app,'CONFIG',{'gates':{name:[sys.executable,'-c','raise SystemExit(5)' if name=='tests' else 'pass'] for name in ('build','tests','security','regression')},'limits':app.CONFIG['limits']}):
            self.assertFalse(app.gates()['passed'])

    def test_benchmark_detects_regression(self):
        with patch.object(app,'plan',return_value={'agents':[],'isolation':'wrong'}):
            self.assertFalse(app.benchmark()['passed'])

    def test_memory_secret_rejection(self):
        with patch.object(sys,'argv',['omega','memory','--title','test','--body','token=do-not-store']):
            with self.assertRaisesRegex(ValueError,'Possible secret'):app.main()

    def test_memory_scoped_and_commit_stamped(self):
        with tempfile.TemporaryDirectory() as d,patch.object(app,'ROOT',Path(d)),patch.object(app,'git',side_effect=lambda *a: '' if a[0] in ('ls-files','check-ignore') else 'abc'):
            dest=app.save('memory',{'title':'ADR','body':'use stdlib'})
            payload=json.loads((Path(d)/dest).read_text())
            self.assertEqual(payload['head'],'abc')
            self.assertEqual(payload['project'],d)
            for invalid in ({'body':'x'*1048576},{'rows':list(range(2001))}):
                with self.assertRaises(ValueError):app.save('memory',invalid)
            self.assertEqual(len(list((Path(d)/'.omega/memory').iterdir())),1)

    def test_dirty_checkout_refused(self):
        with patch.object(sys,'argv',['omega','isolate','--name','test']),patch.object(app,'git',return_value=' M file'):
            with self.assertRaisesRegex(ValueError,'Dirty'):app.main()

    def test_hook_denies_escape_and_policy_edit(self):
        for path in ('/tmp/outside','../outside','.git/config','.claude/agents/test.md','omega/config.json','.env','.env.local'):
            self.assertFalse(authorize({'hook_event_name':'PreToolUse','cwd':str(app.ROOT),'tool_name':'Write','tool_input':{'file_path':path}})[0])

    def test_hook_scoped_edit(self):
        self.assertTrue(authorize({'hook_event_name':'PreToolUse','cwd':str(app.ROOT),'tool_name':'Edit','tool_input':{'file_path':str(app.ROOT/'docs/example.md')}})[0])

    def test_hook_denies_shell_bypass(self):
        for cmd in ('rm -rf /','git status --short; echo bypass','git push','curl https://example.com','python3 -c "print(1)"'):
            self.assertFalse(authorize({'hook_event_name':'PreToolUse','tool_name':'Bash','cwd':str(app.ROOT),'tool_input':{'command':cmd}})[0])

    def test_hook_rejects_malformed(self):
        for payload in (None,{},[],{'hook_event_name':'PreToolUse','tool_name':'Bash','tool_input':None}):
            self.assertFalse(authorize(payload)[0])
        for text in ('{','['*1100+'0'+']'*1100,'{"cwd":"one","cwd":"two"}'):
            p=subprocess.run([sys.executable,'-m','omega.hook'],input=text,text=True,capture_output=True,cwd=app.ROOT)
            self.assertEqual(p.returncode,2);self.assertNotIn('Traceback',p.stderr)

    def test_three_agent_specs(self):
        self.assertEqual(len(list((app.ROOT/'.claude/agents').glob('*.md'))),3)

    def test_candidate_compare_missing_baseline(self):
        with patch.object(sys,'argv',['omega','compare','--baseline','.omega/absent.json']):
            with self.assertRaises((OSError,ValueError)):app.main()

    def test_candidate_lifecycle_preserves_stable(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            from tests.skill_fixture import write_skill
            stable_text=write_skill(root)
            stable=root/'.claude/skills/omega/SKILL.md'
            report={'suite':'test','suite_sha256':'identity','cases':[{'id':'one','passed':True}],'passed':True}
            with patch.object(app,'ROOT',root),patch.object(app,'git',side_effect=lambda *a: '' if a[0] in ('ls-files','check-ignore') else 'abc'),patch.object(app,'benchmark',return_value=report):
                captured=io.StringIO()
                with patch.object(sys,'argv',['omega','candidate','--skill','omega']),contextlib.redirect_stdout(captured):
                    self.assertEqual(app.main(),0)
                result=json.loads(captured.getvalue())
                from omega.skills import HEADINGS
                (root/result['candidate']).write_text(stable_text+'\n'+'\n'.join('## '+h+'\nFixture evidence and limits.' for h in HEADINGS))
                with patch.object(sys,'argv',['omega','compare','--baseline',result['baseline']]),contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(app.main(),0)
                    self.assertEqual(stable.read_text(),stable_text)
                    stable.write_text('unauthorized stable edit')
                    self.assertEqual(app.main(),1)
                    stable.write_text(stable_text)
                    report['suite_sha256']='changed-fixtures'
                    self.assertEqual(app.main(),1)

    def test_git_truncation_refused(self):
        with patch.object(app,'run',return_value={'exit_code':0,'truncated':True,'output':'partial'}):
            with self.assertRaisesRegex(ValueError,'truncated'):app.git('ls-files')


if __name__=='__main__':unittest.main()
