import json
from pathlib import Path
import tempfile
import unittest
from omega.frontmatter import parse
from omega.interop import compatibility,handoff
from omega.analysis_tools import interference,context_check
from omega.skills import assess,HEADINGS
from omega.io import read_json

class InteropSafety(unittest.TestCase):
    def test_metadata_and_multiline_description_safe_subset(self):
        doc=parse('---\nname: sample\ndescription: >\n  First line\n  second line\nlicense: Apache-2.0\nmetadata:\n  version: "1"\n---\nBody')
        self.assertTrue(doc['supported']);self.assertEqual(doc['fields']['metadata'],{'version':'1'})
        self.assertEqual(doc['fields']['description'],'First line second line')
    def test_yaml_tags_and_duplicate_keys_require_review(self):
        for fields in ('name: !execute payload','name: sample\nname: other','metadata:\n  key: one\n  key: two'):
            self.assertFalse(parse('---\n'+fields+'\n---\nBody')['supported'])
    def test_empty_contract_sections_no_longer_score_full(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);path=root/'.omega/candidates/empty.md';path.parent.mkdir(parents=True)
            path.write_text('---\nname: repo-map\ndescription: Fixture\ndisable-model-invocation: true\n---\npython3 -m omega map\npython3 -m omega plan\n'+'\n'.join('## '+h for h in HEADINGS))
            result=assess(root,'repo-map',str(path));self.assertFalse(result['advanced_passed']);self.assertLess(result['score'],100)
            self.assertIsNone(result['quality_score']);self.assertFalse(result['quality_evaluated'])
    def test_skill_bundle_tracks_reference_changes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);path=root/'.omega/candidates/skill.md';path.parent.mkdir(parents=True);(root/'docs').mkdir()
            (root/'docs/guide.md').write_text('Guide A')
            path.write_text('---\nname: repo-map\ndescription: Fixture\ndisable-model-invocation: true\n---\npython3 -m omega map\npython3 -m omega plan\nRead docs/guide.md\n')
            before=assess(root,'repo-map',str(path));(root/'docs/guide.md').write_text('Guide B');after=assess(root,'repo-map',str(path))
            self.assertEqual(before['sha256'],after['sha256']);self.assertNotEqual(before['bundle_sha256'],after['bundle_sha256'])
    def test_json_inputs_reject_duplicates_nan_traversal_and_aliases(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);file=root/'input.json'
            for text in ('{"a":1,"a":2}','{"value":NaN}'):
                file.write_text(text)
                with self.assertRaises(ValueError):read_json(root,'input.json')
            with self.assertRaises(ValueError):read_json(root,'../outside')
            alias=root/'alias.json';alias.symlink_to(file)
            with self.assertRaises(ValueError):read_json(root,'alias.json')
    def test_handoff_rejects_competing_orchestrators(self):
        with tempfile.TemporaryDirectory() as d:
            r=handoff(d,{'nodes':[{'id':'one','role':'orchestrator','owns':['workflow']},{'id':'two','role':'orchestrator','owns':['workflow']}]})
            self.assertFalse(r['passed']);self.assertTrue(any('Multiple owners' in x for x in r['issues']))
    def test_handoff_rejects_cycles_and_unordered_writers(self):
        with tempfile.TemporaryDirectory() as d:
            base={'nodes':[{'id':'main','role':'orchestrator','agents':0},{'id':'a','role':'worker','writes':['app.py']},{'id':'b','role':'worker','writes':['app.py']}]}
            self.assertFalse(handoff(d,base)['passed'])
            base['nodes'][1]['writes']=[];base['nodes'][2]['writes']=[]
            base['nodes'][1]['after']=['b'];base['nodes'][2]['after']=['a']
            self.assertIn('Workflow dependency cycle',handoff(d,base)['issues'])
    def test_handoff_respects_budget_without_claiming_to_spawn(self):
        with tempfile.TemporaryDirectory() as d:
            nodes=[{'id':'main','role':'orchestrator','agents':0}]+[{'id':x,'role':'worker','after':['main']} for x in ('a','b','c')]
            r=handoff(d,{'nodes':nodes,'max_agents':2});self.assertTrue(r['passed']);self.assertEqual(r['schedule'],[['main'],['a','b'],['c']])
    def test_handoff_refuses_path_escape_and_oversized_nodes(self):
        with tempfile.TemporaryDirectory() as d:
            for node in ({'id':'main','role':'orchestrator','writes':['../outside']},{'id':'main','role':'orchestrator','agents':3}):
                with self.assertRaises(ValueError):handoff(d,{'nodes':[node]})
    def test_inspection_does_not_execute_embedded_commands(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);path=root/'skill';path.mkdir();sentinel=root/'NEVER'
            (path/'SKILL.md').write_text('---\nname: sample\ndescription: Fixture\n---\nRun touch '+str(sentinel)+'\n')
            compatibility(root,[str(path)]);self.assertFalse(sentinel.exists())
    def test_inspection_reports_symlink_and_incomplete_root(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'alias').symlink_to('/tmp',target_is_directory=True)
            result=compatibility(root,[str(root/'alias')]);self.assertFalse(result['passed']);self.assertFalse(result['complete_for_selected_roots'])
    def test_hook_inventory_never_echoes_commands_or_secret_strings(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'skills').mkdir();path=root/'hooks.json'
            path.write_text(json.dumps({'hooks':{'Stop':[{'hooks':[{'type':'command','command':'private-value-not-for-output'}]}]}}))
            result=compatibility(root,[str(root/'skills')],[str(path)])
            self.assertNotIn('private-value-not-for-output',json.dumps(result))
    def runs(self):
        return {'runs':[{'task_id':'t','trial':0,'arm':arm,'model':'m','model_version':'v','prompt_sha256':'a'*64,'acceptance':{'correct':True},'provenance':'fixture'} for arm in ('A','B','A+B')]}
    def test_interference_rejects_missing_arm_changed_prompt_and_model(self):
        for kind in ('missing','prompt','model','criteria','duplicate'):
            d=self.runs()
            if kind=='missing':d['runs'].pop()
            elif kind=='prompt':d['runs'][0]['prompt_sha256']='b'*64
            elif kind=='model':d['runs'][0]['model']='other'
            elif kind=='criteria':d['runs'][0]['acceptance']={'different':True}
            else:d['runs'].append(dict(d['runs'][0]))
            with self.assertRaises(ValueError):interference(d)
    def test_fixture_results_cannot_authorize_native_release(self):
        report=interference(self.runs());self.assertTrue(report['passed']);self.assertFalse(report['native_measurements_present']);self.assertFalse(report['native_release_eligible'])
    def test_usage_unknown_is_not_reported_as_zero(self):
        report=interference(self.runs());self.assertIsNone(report['arms']['A']['tokens_mean'])
