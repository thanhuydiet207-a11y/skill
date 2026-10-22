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
        for fields in ('name: !execute payload','name: sample\nname: other','metadata:\n  key: one\n  key: two','disable-model-invocation: true # native YAML comment'):
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
        return {'runs':[{'task_id':'t','trial':0,'arm':arm,'model':'m','model_version':'v','grader_version':'fixture-v1','skill_bundles':{label:('a' if label=='A' else 'b')*64 for label in (('A','B') if arm=='A+B' else (arm,))},'prompt_sha256':'a'*64,'acceptance':{'correct':True},'provenance':'fixture'} for arm in ('A','B','A+B')]}
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

class ReviewRegressions(unittest.TestCase):
    def test_interference_bundle_identity_fixed_across_arms(self):
        d=self.runs();d['runs'][2]['skill_bundles']['A']='c'*64
        with self.assertRaisesRegex(ValueError,'bundle changed'):interference(d)
    def test_interference_grader_and_bundle_provenance_required(self):
        for change in ('grader','missing-bundle','extra-bundle'):
            d=self.runs()
            if change=='grader':d['runs'][0]['grader_version']='other'
            elif change=='missing-bundle':d['runs'][0].pop('skill_bundles')
            else:d['runs'][0]['skill_bundles']['B']='b'*64
            with self.assertRaises(ValueError):interference(d)
    def test_inspection_refuses_symlink_in_root_ancestry(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'real/skills').mkdir(parents=True);(root/'alias').symlink_to(root/'real',target_is_directory=True)
            self.assertFalse(compatibility(root,['alias/skills'])['complete_for_selected_roots'])
    def test_hook_inspection_handles_depth_and_size_budgets_without_execution(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'skills').mkdir();p=root/'hooks.json'
            for text in ('['*1100+'0'+']'*1100,json.dumps({'hooks':{'Stop':[{'hooks':[{'type':'command','command':'never'}]*129}]}})):
                p.write_text(text);result=compatibility(root,['skills'],['hooks.json'])
                self.assertFalse(result['passed']);self.assertFalse(result['complete_for_selected_roots'])
    def test_configured_concurrency_cap_is_respected(self):
        with tempfile.TemporaryDirectory() as d:
            doc={'nodes':[{'id':'main','role':'orchestrator','agents':0}]+[{'id':x,'role':'worker','after':['main']} for x in ('a','b')]}
            self.assertEqual(handoff(d,doc,1)['schedule'],[['main'],['a'],['b']])
            with self.assertRaises(ValueError):handoff(d,{**doc,'max_agents':2},1)
    def test_context_task_requires_object_instead_of_crashing(self):
        for malformed in (None,[],True,'bad'):
            with self.assertRaises(ValueError):context_check(Path('/tmp'),{'requirements':{},'packet':{'task':malformed}})
    def test_context_source_read_is_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'large.py').write_bytes(b'x'*1_000_001)
            doc={'requirements':{'acceptance':['works'],'constraints':[],'sources':[{'path':'large.py','start':1,'end':1}]},
                 'packet':{'task':{'acceptance':['works'],'constraints':[]},'sources':[{'path':'large.py','start':1,'end':1}]}}
            with self.assertRaisesRegex(ValueError,'oversized'):context_check(root,doc)
    def test_non_orchestrator_cannot_declare_zero_agent_cost(self):
        with tempfile.TemporaryDirectory() as d:
            doc={'nodes':[{'id':'main','role':'orchestrator','agents':0},{'id':'worker','role':'worker','agents':0}]}
            with self.assertRaises(ValueError):handoff(d,doc)
    def test_duplicate_ownership_declarations_refused(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):handoff(d,{'nodes':[{'id':'main','role':'orchestrator','owns':['git','git']}]})
    def runs(self):
        return {'runs':[{'task_id':'task','trial':0,'arm':a,'model':'fixture','model_version':'1','grader_version':'fixture-v1','skill_bundles':{label:('a' if label=='A' else 'b')*64 for label in (('A','B') if a=='A+B' else (a,))},'prompt_sha256':'a'*64,'acceptance':{'works':True},'provenance':'fixture'} for a in ('A','B','A+B')]}
    def test_different_tasks_can_have_different_fixed_acceptance(self):
        d=self.runs();other=json.loads(json.dumps(d['runs']))
        for run in other:run.update(task_id='other',acceptance={'different-contract':True},prompt_sha256='b'*64)
        d['runs']+=other;self.assertTrue(interference(d)['passed'])
    def test_prompt_is_fixed_across_repeated_trials(self):
        d=self.runs();other=json.loads(json.dumps(d['runs']))
        for run in other:run.update(trial=1,prompt_sha256='b'*64)
        d['runs']+=other
        with self.assertRaises(ValueError):interference(d)
    def test_no_regression_is_not_enough_when_combined_acceptance_fails(self):
        d=self.runs()
        for run in d['runs']:run['acceptance']['works']=False
        result=interference(d);self.assertTrue(result['non_regression']);self.assertFalse(result['passed']);self.assertFalse(result['all_combined_acceptance_passed'])
    def test_huge_or_boolean_measurements_refused(self):
        for value in (True,10**100):
            d=self.runs();d['runs'][0]['tokens']=value
            with self.assertRaises(ValueError):interference(d)
    def test_duplicate_hook_json_is_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'skills').mkdir();(root/'hooks.json').write_text('{"hooks":{},"hooks":{}}')
            r=compatibility(root,[str(root/'skills')],[str(root/'hooks.json')]);self.assertFalse(r['passed']);self.assertFalse(r['complete_for_selected_roots'])
    def test_unknown_hook_type_needs_review_without_echoing_value(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'skills').mkdir();(root/'hooks.json').write_text(json.dumps({'hooks':{'Stop':[{'hooks':[{'type':'sensitive-unknown-value'}]}]}}))
            r=compatibility(root,[str(root/'skills')],[str(root/'hooks.json')]);self.assertFalse(r['passed']);self.assertNotIn('sensitive-unknown-value',json.dumps(r))
