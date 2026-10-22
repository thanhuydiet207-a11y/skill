"""OMEGA: local, dependency-free engineering evidence tools (not an LLM runtime)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / 'omega/config.json').read_text())


def confined(path):
    p = (ROOT / path).resolve()
    if not p.is_relative_to(ROOT) or p == ROOT:
        raise ValueError('Path must be strictly inside repository')
    return p


def run(argv, timeout=120):
    from omega.process import execute
    return execute(argv,ROOT,timeout,CONFIG['limits']['max_evidence_bytes'],
                   CONFIG['limits'].get('max_output_bytes',1048576))


def git(*args, raw=False):
    result = run(['git', *args])
    if result['truncated']:
        raise ValueError('Git control output truncated; operation refused, narrow scope or increase reviewed limit')
    if result.get('invalid_utf8'):
        raise ValueError('Git output is not valid UTF-8; operation refused')
    if result['exit_code']:
        raise ValueError(result['output'])
    return result['output'] if raw else result['output'].strip()


def save(kind, data):
    from omega.safety import artifact_path
    directory = artifact_path(ROOT,'.omega/' + kind + '/placeholder',kind,False).parent
    directory.mkdir(parents=True, exist_ok=True)
    dest = confined(str(directory.relative_to(ROOT) / (str(time.time_ns())+'-'+uuid.uuid4().hex[:8]+'.json')))
    payload = {'schema': 1, 'project': str(ROOT), 'head': git('rev-parse','HEAD'),
               'created_utc': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(), **data}
    with os.fdopen(os.open(dest,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'w',encoding='utf-8') as out:
        out.write(json.dumps(payload, indent=2, ensure_ascii=False)+'\n')
    return str(dest.relative_to(ROOT))


def plan(complexity, conflict=False):
    roles = {'low': [], 'medium': ['omega-engineer','omega-verifier'],
             'high': ['omega-investigator','omega-engineer','omega-verifier']}
    return {'complexity': complexity, 'agents': roles[complexity],
            'schedule': 'sequential; parallel only independent read tasks',
            'max_concurrent_agents': 2, 'isolation': 'worktree' if conflict else 'branch',
            'skills': ['repo-map','controlled-change','quality-gates','project-memory'],
            'limits': CONFIG['limits'], 'execution': 'manual Claude orchestration; no API calls'}


def inventory():
    paths = [x for x in git('ls-files','-z','--cached','--others','--exclude-standard',raw=True).split('\0') if x]
    safe, skipped = [], []
    used = 0
    for name in dict.fromkeys(paths):
        try:
            p = confined(name)
            if not p.is_file():
                continue
            entry = {'path': name, 'bytes': p.stat().st_size}
            if used + len(json.dumps(entry)) > CONFIG['limits']['max_context_bytes']:
                skipped.append(name)
                continue
            safe.append(entry)
            used += len(json.dumps(entry))
        except ValueError:
            skipped.append(name)
    return {'files': safe, 'omitted': skipped, 'status': git('status','--short'),
            'note': 'Metadata only; no file contents or credential discovery'}


def doctor():
    binary = shutil.which('claude')
    return {'python': sys.version.split()[0], 'git': git('--version'),
            'claude': run([binary,'--version']) if binary else {'available':False},
            'native_integration': 'UNVERIFIED: verify skills, agents, hook schemas and permissions with installed Claude help/docs',
            'hooks_enabled': False, 'mcp_enabled': False}


def audit():
    findings = []
    # Narrow source policy scan, NOT a vulnerability or secret scanner.
    for p in (ROOT / '.claude').rglob('*'):
        if p.is_file():
            path = confined(str(p.relative_to(ROOT)))
            text = path.read_text()
            for forbidden in ('--dangerously-skip-permissions', '"bypassPermissions"', 'curl -k ', 'verify=False'):
                if forbidden in text:
                    findings.append({'path': str(p.relative_to(ROOT)), 'rule': forbidden})
    return {'passed': not findings, 'findings': findings,
            'scope': 'Claude config bypass patterns only; no dependency/SAST/secret coverage'}


def benchmark():
    cases = json.loads((ROOT/'benchmarks/cases.json').read_text())
    results = []
    for case in cases:
        actual = plan(case['complexity'],case['conflict'])
        results.append({'id':case['id'], 'passed':all(actual[k] == case[k] for k in ('agents','isolation'))})
    suite_hash = hashlib.sha256((ROOT/'benchmarks/cases.json').read_bytes() + Path(__file__).read_bytes()).hexdigest()
    return {'suite':'router-contract-v1','suite_sha256':suite_hash,'cases':results,'passed':bool(results) and all(x['passed'] for x in results),
            'scope':'deterministic router contract only; native LLM skill efficacy not evaluated'}


def validate_gates():
    commands=CONFIG.get('gates')
    required={'build','tests','security','regression'}
    if not isinstance(commands,dict) or not required.issubset(commands):
        raise ValueError('Missing required gates: build, tests, security, regression')
    for name,argv in commands.items():
        if not isinstance(name,str) or not name or not isinstance(argv,list) or not argv or any(not isinstance(x,str) or not x or '\0' in x for x in argv):
            raise ValueError('Invalid gate argv')
    seconds=CONFIG['limits']['max_gate_seconds']
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not 0 < seconds <= 600:
        raise ValueError('Gate timeout must be between 0 and 600 seconds')


def gates():
    validate_gates()  # Validate ALL policy before executing the first command.
    from omega.records import workspace
    before=workspace(ROOT,git)
    results=[]
    for name,argv in CONFIG['gates'].items():
        result=run(argv, CONFIG['limits']['max_gate_seconds'])
        results.append({'gate':name,**result})
    after=workspace(ROOT,git)
    return {'passed':bool(results) and before==after and all(r['exit_code']==0 for r in results),
            'workspace_sha256':before,'workspace_unchanged':before==after,'results':results}


def fingerprint(skill):
    if skill not in {p.name for p in (ROOT/'.claude/skills').iterdir() if p.is_dir()}:
        raise ValueError('Unknown implemented skill')
    return hashlib.sha256(confined(f'.claude/skills/{skill}/SKILL.md').read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['doctor','map','plan','audit','benchmark','gates','memory','isolate','rollback-check','candidate','compare','context','memory-read','change-plan','change-check','change-attempt'])
    parser.add_argument('--complexity',choices=['low','medium','high'],default='low')
    parser.add_argument('--conflict',action='store_true')
    parser.add_argument('--title');parser.add_argument('--body');parser.add_argument('--name')
    parser.add_argument('--worktree');parser.add_argument('--skill');parser.add_argument('--baseline');parser.add_argument('--candidate')
    parser.add_argument('--compact',action='store_true',help='Lossless compact JSON')
    parser.add_argument('--summary',action='store_true',help='Gates only: logs by evidence reference; failures inline')
    parser.add_argument('--select',action='append',default=[],help='Explicit source PATH or PATH:START:END')
    parser.add_argument('--max-bytes',type=int,default=24000)
    parser.add_argument('--record');parser.add_argument('--reason')
    parser.add_argument('--allow',action='append',default=[])
    parser.add_argument('--acceptance',action='append',default=[])
    parser.add_argument('--evidence',action='append',default=[])
    args=parser.parse_args()
    if args.summary and args.command != 'gates': parser.error('--summary requires gates')
    code=0
    if args.command=='context':
        from omega.context import packet
        result=packet(ROOT,args.select,args.max_bytes)
    elif args.command=='doctor': result=doctor()
    elif args.command=='map': result=inventory()
    elif args.command=='plan':result=plan(args.complexity,args.conflict)
    elif args.command=='audit':
        result=audit();code=0 if result['passed'] else 1
    elif args.command=='benchmark':
        result=benchmark();code=0 if result['passed'] else 1
    elif args.command=='gates':
        result=gates();code=0 if result['passed'] else 1
        result['evidence']=save('evidence',result)
        if args.summary:
            from omega.context import gate_summary
            result=gate_summary(result)
    elif args.command=='memory-read':
        from omega.records import memory_status
        if not args.record:raise ValueError('--record required')
        result=memory_status(ROOT,args.record,git('rev-parse','HEAD'))
        code=1 if result['stale'] else 0
    elif args.command=='change-plan':
        from omega.change import create
        result=create(ROOT,git,args.allow,args.acceptance,CONFIG['limits'])
        result={'record':save('changes',result),**result}
    elif args.command=='change-check':
        from omega.change import check
        if not args.record:raise ValueError('--record required')
        result=check(ROOT,args.record,git,CONFIG['limits'],args.evidence)
        code=0 if result['passed'] else 1
    elif args.command=='change-attempt':
        from omega.change import attempt
        if not args.record:raise ValueError('--record required')
        result=attempt(ROOT,args.record,args.reason,CONFIG['limits'])
    elif args.command=='memory':
        if not args.title or not args.body: raise ValueError('--title and --body required')
        text=args.title+' '+args.body
        if len(text.encode())>8000: raise ValueError('Memory exceeds 8000 bytes')
        if re.search(r'(?i)(sk-[a-z0-9_-]{12,}|gh[pousr]_[a-z0-9]{12,}|-----BEGIN .*PRIVATE KEY|(?:password|token|secret|api_key)\s*[:=]\s*\S+)',text):
            raise ValueError('Possible secret; redact before storing')
        from omega.records import memory_payload
        result={'memory':save('memory',memory_payload(ROOT,args.title,args.body,args.select,args.evidence))}
    elif args.command=='isolate':
        if not args.name or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,60}',args.name): raise ValueError('Invalid branch name')
        if git('status','--porcelain'): raise ValueError('Dirty checkout: preserve changes before isolation')
        branch='omega/'+args.name
        if args.worktree:
            p=confined(args.worktree)
            if not p.is_relative_to(confined('.omega/worktrees')): raise ValueError('Worktree must be below .omega/worktrees')
            if p.exists():raise ValueError('Destination exists')
            result={'output':git('worktree','add','-b',branch,str(p),'HEAD')}
        else:result={'output':git('switch','-c',branch)}
    elif args.command=='rollback-check':
        result={'head':git('rev-parse','--verify','HEAD^{commit}'), 'diff_check':run(['git','diff','--check']),
                'strategy':'Review diff and use explicit approved revert commit. No automatic reset, clean, delete or revert.',
                'runtime_rollback':'not applicable: no deployed service or migration'}
        code=0 if result['diff_check']['exit_code']==0 else 1
    elif args.command=='candidate':
        result={'skill':args.skill,'sha256':fingerprint(args.skill),'benchmark':benchmark(),
                'promotion':'manual only; gates plus review required'}
        candidate = confined('.omega/candidates/' + args.skill + '-' + uuid.uuid4().hex + '.md')
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_bytes(confined(f'.claude/skills/{args.skill}/SKILL.md').read_bytes())
        result['candidate'] = str(candidate.relative_to(ROOT))
        result['baseline']=save('baselines',result)
        code=0 if result['benchmark']['passed'] else 1
    else:
        if not args.baseline:raise ValueError('--baseline required')
        baseline=json.loads(confined(args.baseline).read_text())
        current=benchmark()
        same_suite=baseline['benchmark'].get('suite_sha256')==current['suite_sha256'] and baseline['benchmark']['suite']==current['suite'] and [x['id'] for x in baseline['benchmark']['cases']]==[x['id'] for x in current['cases']]
        candidate = confined(args.candidate or baseline['candidate'])
        if not candidate.is_relative_to(confined('.omega/candidates')) or not candidate.is_file():
            raise ValueError('Candidate must be an existing file in .omega/candidates')
        stable_modified = baseline['sha256'] != fingerprint(baseline['skill'])
        passed=same_suite and not stable_modified and baseline['benchmark']['passed'] and current['passed']
        result={'passed':passed,'skill':baseline['skill'],'before':baseline['sha256'],
                'after':hashlib.sha256(candidate.read_bytes()).hexdigest(),'benchmark':current,'stable_modified':stable_modified,
                'promotion':'not performed; native evaluation and human review still required'}
        code=0 if passed else 1
    from omega.context import encode
    print(encode(result,args.compact))
    return code


if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print(json.dumps({'error':str(exc)}),file=sys.stderr);sys.exit(2)
