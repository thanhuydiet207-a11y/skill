import json
from pathlib import Path
import tempfile
import unittest
from benchmarks.eval_metrics import load, summarize


def run(score,passed,cost,trace=None,indicators=()):
    return {'score':score,'passed':passed,'costUsd':cost,'durationSeconds':10,'turns':3,'error':None,'tracePath':trace,
            'graders':[{'name':n,'passed':True,'withOnly':True} for n in indicators]}


class EvalMetrics(unittest.TestCase):
    def results(self,root):
        trace=root/'trace.jsonl'
        events=[{'type':'assistant','message':{'content':[{'type':'tool_use','name':'Skill','input':{'skill':'omega:omega'}},
                                                         {'type':'tool_use','name':'Bash','input':{'command':'ls'}}]}},
                {'type':'assistant','message':{'content':[{'type':'tool_use','name':'Bash','input':{}},{'type':'text','text':'done'}]}},
                {'type':'result','usage':{'input_tokens':2,'cache_read_input_tokens':100,'cache_creation_input_tokens':50,'output_tokens':40},
                 'modelUsage':{'claude-test':{}},'subagent_stats':{'spawned':0}}]
        trace.write_text('\n'.join(json.dumps(e) for e in events)+'\nnot json\n')
        data={'claudeVersion':'0.0.0','startedAt':'t','cases':[
            {'name':'fix','dir':'evals/fix','arms':{'with':[run(1,True,0.2,str(trace),['used-skill']),run(0,False,0.1)],
                                                 'without':[run(1,True,0.1,str(root/'missing.jsonl'))]}},
            {'name':'fix','dir':'.omega/plugin-packaging/runs/x/marketplace/evals/fix','arms':{'with':[run(0,False,0)]}}]}
        (root/'aggregate-result.json').write_text(json.dumps(data))

    def test_tokens_tools_and_skills_come_from_the_trace_result(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.results(root)
            meta,rows=load('current',root)
            self.assertEqual(meta['claude_version'],'0.0.0');self.assertEqual(len(rows),3)  # Stale .omega copy skipped.
            traced=rows[0]
            self.assertEqual(traced['tokens'],{'input':2,'cache_read':100,'cache_write':50,'output':40})
            self.assertEqual(traced['tool_calls'],{'Skill':1,'Bash':2});self.assertEqual(traced['skills'],{'omega:omega':1})
            self.assertEqual(traced['indicators'],{'used-skill':True})
            self.assertIsNone(rows[1]['tokens']);self.assertIsNone(rows[2]['tokens'])  # No trace: no token figure.

    def test_summary_reports_cost_per_success_and_only_traced_tokens(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.results(root)
            _,rows=load('current',root)
            with_arm,without_arm=summarize(rows)
            self.assertEqual((with_arm['arm'],with_arm['runs'],with_arm['success_rate']),('with',2,0.5))
            self.assertEqual(with_arm['cost_per_success_usd'],0.3)
            self.assertEqual((with_arm['runs_with_tokens'],with_arm['mean_input_tokens'],with_arm['mean_output_tokens']),(1,152,40))
            self.assertEqual((with_arm['mean_tool_calls'],with_arm['skill_invocation_rate']),(3,1.0))
            self.assertEqual(without_arm['runs_with_tokens'],0);self.assertIsNone(without_arm['mean_input_tokens'])


if __name__=='__main__':unittest.main()
