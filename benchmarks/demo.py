"""Reproducible broken -> isolated fix -> green workflow, entirely in .omega/demo.
No network, no user data deletion, no push, no LLM claims.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ROOT=Path(__file__).resolve().parent.parent


def main():
    base=(ROOT/'.omega/demo').resolve()
    if not base.is_relative_to(ROOT):raise ValueError('Unsafe demo path')
    base.mkdir(parents=True,exist_ok=True)
    fixture=base/uuid.uuid4().hex
    fixture.mkdir()
    for name in ('omega','benchmarks','.claude','docs'):
        shutil.copytree(ROOT/name,fixture/name,ignore=shutil.ignore_patterns('__pycache__','evidence'))
    (fixture/'.gitignore').write_text('.omega/\n__pycache__/\n')
    (fixture/'calc.py').write_text('def add(a,b):\n    return a-b\n')
    (fixture/'checks').mkdir()
    (fixture/'checks/test_calc.py').write_text('import unittest\nfrom calc import add\nclass Calc(unittest.TestCase):\n    def test_add(self): self.assertEqual(add(2,3),5)\n')
    config=json.loads((fixture/'omega/config.json').read_text())
    config['gates']['build']=[sys.executable,'-m','compileall','-q','-f','--invalidation-mode','checked-hash','calc.py']
    config['gates']['tests']=[sys.executable,'-m','omega.test_runner','--start','checks']
    (fixture/'omega/config.json').write_text(json.dumps(config))

    def execute(argv,expected=0):
        proc=subprocess.run(argv,cwd=fixture,capture_output=True,text=True,timeout=30)
        if proc.returncode!=expected:
            raise RuntimeError(f'{argv}: expected {expected}, got {proc.returncode}: {proc.stderr} {proc.stdout}')
        return proc

    def cli(*args,expected=0):
        return json.loads(execute([sys.executable,'-m','omega',*args],expected).stdout)

    execute(['git','init','-q'])
    execute(['git','add','.'])
    execute(['git','-c','user.name=OMEGA fixture','-c','user.email=omega@example.invalid','commit','-qm','broken baseline fixture'])
    baseline=execute(['git','rev-parse','HEAD']).stdout.strip()
    before=cli('gates',expected=1)
    assert next(x for x in before['results'] if x['gate']=='tests')['exit_code']!=0
    cli('isolate','--name','demo-fix')
    (fixture/'calc.py').write_text('def add(a,b):\n    return a+b\n')
    after=cli('gates')
    assert after['passed']
    memory=cli('memory','--title','Addition fix','--body','Reproduced wrong subtraction, changed to addition; tests now pass. Evidence '+after['evidence'])
    rollback=cli('rollback-check')
    original=execute(['git','show',baseline+':calc.py']).stdout
    assert 'a-b' in original
    # An independent worktree remains on baseline; no cleanup/delete is automated.
    execute(['git','add','calc.py'])
    execute(['git','-c','user.name=OMEGA fixture','-c','user.email=omega@example.invalid','commit','-qm','fix addition fixture'])
    cli('isolate','--name','parallel','--worktree','.omega/worktrees/parallel')
    candidate=cli('candidate','--skill','repo-map')
    candidate_path=fixture/candidate['candidate']
    candidate_path.write_text(candidate_path.read_text()+'\nCandidate note: evidence before conclusions.\n')
    comparison=cli('compare','--baseline',candidate['baseline'])
    result={'fixture':str(fixture.relative_to(ROOT)), 'baseline_commit':baseline,
            'before_passed':before['passed'],'after_passed':after['passed'],
            'regression_tests':1,'isolated_branch':'omega/demo-fix','worktree_created':True,
            'baseline_recoverable':True,'memory':memory['memory'],
            'candidate_passed':comparison['passed'],'stable_modified':comparison['stable_modified'],
            'rollback_diff_exit':rollback['diff_check']['exit_code'],
            'native_claude_executed':False,'network_used':False}
    report=fixture/'demo-result.json'
    report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0


if __name__=='__main__':sys.exit(main())
