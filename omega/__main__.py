"""OMEGA: local, dependency-free engineering evidence tools (not an LLM runtime)."""
import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
import uuid

ENGINE_ROOT = Path(__file__).resolve().parent.parent
ROOT = ENGINE_ROOT
CONFIG = json.loads((ROOT / 'omega/config.json').read_text())


def confined(path):
    p = (ROOT / path).resolve()
    if not p.is_relative_to(ROOT) or p == ROOT:
        raise ValueError('Path must be strictly inside repository')
    return p


def run(argv, timeout=120, capture_bytes=None):
    from omega.process import execute
    return execute(argv,ROOT,timeout,capture_bytes or CONFIG['limits']['max_evidence_bytes'],
                   CONFIG['limits'].get('max_output_bytes',1048576))


def git(*args, raw=False):
    result = run(['git', *args],capture_bytes=min(1048576,CONFIG['limits'].get('max_output_bytes',1048576)))
    if result['truncated']:
        raise ValueError('Git control output truncated; operation refused, narrow scope or increase reviewed limit')
    if result.get('invalid_utf8'):
        raise ValueError('Git output is not valid UTF-8; operation refused')
    if result['exit_code']:
        raise ValueError(result['output'])
    return result['output'] if raw else result['output'].strip()


def runtime_ready():
    # Do not create project evidence where it could silently enter source control.
    try:git('check-ignore','--quiet','--','.omega/OMEGA_RUNTIME_CHECK')
    except ValueError as exc:raise ValueError('Runtime state requires reviewed .omega/ ignore; no ignore file was changed') from exc
    if git('ls-files','--','.omega'):
        raise ValueError('Tracked .omega state refused; review existing tracked data before writing runtime state')


def save(kind, data):
    from omega.safety import artifact_path
    runtime_ready()
    directory = artifact_path(ROOT,'.omega/' + kind + '/placeholder',kind,False).parent
    dest = confined(str(directory.relative_to(ROOT) / (str(time.time_ns())+'-'+uuid.uuid4().hex[:8]+'.json')))
    payload = {'schema': 1, 'project': str(ROOT), 'head': git('rev-parse','HEAD'),
               'created_utc': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(), **data}
    encoded=json.dumps(payload,indent=2,ensure_ascii=False)+'\n'
    from omega.io import bounded_json
    bounded_json(encoded)  # Refuse a record that the bounded reader could not load.
    directory.mkdir(parents=True, exist_ok=True)
    with os.fdopen(os.open(dest,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'w',encoding='utf-8') as out:
        out.write(encoded)
        out.flush();os.fsync(out.fileno())
    return str(dest.relative_to(ROOT))


def plan(complexity, conflict=False, intent="change", workflow=None):
    roles = {'low': [], 'medium': ['omega-engineer','omega-verifier'],
             'high': ['omega-investigator','omega-engineer','omega-verifier']}
    selections={
        'change':['repo-map','controlled-change','quality-gates','project-memory'],
        'investigate':['repo-map','omega-context-sufficiency-check'],
        'verify':['quality-gates','omega-evidence-reconciler'],
        'knowledge':['project-memory','omega-memory-reconciliation'],
        'evolve':['skill-benchmark','omega-skill-interference-benchmark'],
        'interoperability':['omega-skill-compatibility-audit','omega-effective-policy-explainer','omega-workflow-handoff-contract']}
    if intent not in selections or complexity not in roles or type(conflict) is not bool:raise ValueError('Invalid plan intent/complexity/conflict')
    contract=None
    if workflow is not None:
        from omega.interop import handoff
        contract=handoff(ROOT,workflow,CONFIG['limits']['max_agents'])
    from omega.skills import MODES
    modes=selections[intent]
    return {'complexity': complexity,'intent':intent,'workflow_contract':contract, 'agents': roles[complexity],
            'schedule': 'sequential; parallel only independent read tasks',
            'max_concurrent_agents': min(2,CONFIG['limits']['max_agents']), 'isolation': 'worktree' if conflict else 'branch',
            'skills':['omega'],'modes':modes,
            'reference_root':str(ENGINE_ROOT),
            'references':[f'.claude/skills/omega/{MODES[name]["reference"]}' for name in modes],
            'selection':'one omega entry; explicit intent selects reference metadata only; no automatic agent dispatch',
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
            kind='manifest' if p.name in ('package.json','pyproject.toml','requirements.txt','go.mod','Cargo.toml','pom.xml') or 'lock' in p.name else 'ci' if name.startswith('.github/workflows/') else 'test' if 'tests' in p.parts or p.name.startswith('test_') else 'documentation' if p.suffix=='.md' else 'source' if p.suffix in ('.py','.js','.ts','.go','.rs','.java','.tsx','.jsx') else 'other'
            entry = {'path': name, 'bytes': p.stat().st_size,'kind':kind}
            if used + len(json.dumps(entry)) > CONFIG['limits']['max_context_bytes']:
                skipped.append(name)
                continue
            safe.append(entry)
            used += len(json.dumps(entry))
        except ValueError:
            skipped.append(name)
    status=git('status','--short')
    result={'files': safe, 'omitted': skipped[:20], 'omitted_count':len(skipped),'omitted_list_truncated':len(skipped)>20,
            'status':status[:4000], 'status_truncated':len(status)>4000,
            'note': 'Metadata only; no file contents or credential discovery'}
    # Bound the full JSON envelope, including long escaped paths and status.
    def fits():return len(json.dumps(result,ensure_ascii=False,indent=2).encode())<=CONFIG['limits']['max_context_bytes']
    while result['files'] and not fits():
        removed=result['files'].pop()['path'];result['omitted_count']+=1
        if len(result['omitted'])<20:result['omitted'].append(removed)
        result['omitted_list_truncated']=result['omitted_count']>len(result['omitted'])
    while result['omitted'] and not fits():
        result['omitted'].pop();result['omitted_list_truncated']=True
    while result['status'] and not fits():
        result['status']=result['status'][:len(result['status'])//2];result['status_truncated']=True
    if not fits():raise ValueError('Inventory byte budget too small for metadata envelope')
    return result


def doctor():
    from omega.process import execute
    from omega.safety import artifact_path
    binary=shutil.which('claude');source='PATH' if binary else None
    local=ROOT/'.omega/tools/claude/node_modules/.bin/claude'
    if not binary and local.is_file() and local.resolve().is_relative_to((ROOT/'.omega/tools/claude').resolve()):
        binary=str(local);source='project-local'
    native={'available':False}
    if binary:
        runtime_ready()
        state=artifact_path(ROOT,'.omega/claude-state/runtime.marker','claude-state',False).parent
        try:state.mkdir(parents=True,exist_ok=True)
        except OSError:state=None  # Read-only checkout: probe with a throwaway config dir instead.
        with tempfile.TemporaryDirectory() as scratch:
            environment=dict(os.environ);environment['CLAUDE_CONFIG_DIR']=str(state or scratch)
            native={'available':True,'source':source,**execute([binary,'--version'],ROOT,timeout=15,env=environment)}
    return {'python':sys.version.split()[0],'git':git('--version'),'claude':native,
            'native_integration':'Version probe only; skills, agents and hook behavior remain UNVERIFIED',
            'hooks_enabled':'unknown','mcp_enabled':'unknown',
            'project_settings_present':(ROOT/'.claude/settings.json').exists(),
            'effective_policy':'Not resolved: user, managed and plugin settings were not inspected'}


def audit(selections=()):
    from omega.security import audit as inspect
    return inspect(ROOT,selections)


def benchmark():
    cases = json.loads((ROOT/'benchmarks/cases.json').read_text())
    results = []
    for case in cases:
        actual = plan(case['complexity'],case['conflict'])
        results.append({'id':case['id'], 'passed':all(actual[k] == case[k] for k in ('agents','isolation'))})
    from omega.skills import assess, suite_digest, COMMANDS, MODES
    skills=[assess(ROOT,name) for name in COMMANDS]
    suite_hash = suite_digest(ROOT)
    return {'suite':'router-contract-v2','suite_sha256':suite_hash,'cases':results,'skills':skills,'mode_count':len(MODES),'passed':bool(results) and all(x['passed'] for x in results) and all(x['passed'] for x in skills),
            'scope':'router and offline skill contracts; native LLM skill efficacy not evaluated'}


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
    from omega.reports import validate_policy
    validate_policy(CONFIG)


def gates():
    validate_gates()  # Validate ALL policy before executing the first command.
    from omega.records import workspace, test_outcomes
    from omega.records import execution_context
    before=workspace(ROOT,git);execution=execution_context(ROOT,CONFIG)
    from omega.reports import materialize,read_report,still_unchanged
    if CONFIG.get('test_report') is not None:runtime_ready()
    commands,report_spec=materialize(ROOT,CONFIG)
    results=[]
    for name,argv in commands.items():
        result=run(argv, CONFIG['limits']['max_gate_seconds'])
        if name=='tests' and report_spec is not None:
            result['configured_command']=CONFIG['gates'][name]
            try:result['report']=read_report(ROOT,report_spec)
            except (ValueError,OSError):result['report']={**report_spec,'fresh':False,'unchanged':False,'error':'Missing, unsafe, oversized or unstable report'}
        results.append({'gate':name,**result})
    after=workspace(ROOT,git)
    test_row=next(r for r in results if r['gate']=='tests')
    test_row['adapter']=CONFIG.get('test_adapter','omega')
    if report_spec is not None and test_row['report'].get('fresh') is True:test_row['report']['unchanged']=still_unchanged(ROOT,test_row['report'])
    counts=test_outcomes(test_row)
    return {'kind':'gates','test_adapter':CONFIG.get('test_adapter','omega'),'test_report':CONFIG.get('test_report'),'test_outcomes':counts,'execution_fingerprint':execution['sha256'],'execution_context':execution['details'],
            'execution_unchanged':execution['sha256']==execution_context(ROOT,CONFIG)['sha256'],
            'passed':bool(results) and counts is not None and before==after and execution['sha256']==execution_context(ROOT,CONFIG)['sha256'] and all(r['exit_code']==0 for r in results),
            'workspace_sha256':before,'workspace_unchanged':before==after,'results':results}


def fingerprint(skill):
    from omega.skills import COMMANDS
    if skill not in COMMANDS:
        raise ValueError('Only unified skill omega is registered; use --skill omega')
    from omega.safety import source_path
    return hashlib.sha256(source_path(ROOT,f'.claude/skills/{skill}/SKILL.md').read_bytes()).hexdigest()


def _dispatch():
    global ROOT, CONFIG
    from omega.arguments import parser as make_parser,validate
    parser=make_parser();args=parser.parse_args();validate(args)
    if args.project_root:
        target=Path(args.project_root)
        if not target.is_absolute() or not target.is_dir():raise ValueError('Project root must be an existing absolute directory')
        ROOT=target.resolve()
        # Checked before running git so the hint does not depend on git's (localizable) error text.
        if not any((p/'.git').exists() for p in (ROOT,*ROOT.parents)):raise ValueError('Project root is not a Git repository; OMEGA evidence is tied to Git HEAD. Run git init and make a first commit, then retry')
        if Path(git('rev-parse','--show-toplevel')).resolve()!=ROOT:raise ValueError('Project root must equal its Git checkout root')
    if args.gate_config:
        from omega.io import read_json
        from omega.safety import artifact_path
        artifact_path(ROOT,args.gate_config,'configs')
        policy=read_json(ROOT,args.gate_config)
        if not isinstance(policy,dict) or type(policy.get('schema')) is not int or policy.get('schema')!=1 or set(policy)-{'schema','gates','test_adapter','runtime_inputs','test_report'}:raise ValueError('Invalid gate policy schema')
        if policy.get('test_adapter','omega') not in ('omega','go','jest','junit'):raise ValueError('Unknown test adapter')
        CONFIG={**CONFIG,'gates':policy.get('gates'),'test_adapter':policy.get('test_adapter','omega'),'runtime_inputs':policy.get('runtime_inputs',[]),'test_report':policy.get('test_report')}
    if ROOT!=ENGINE_ROOT and args.project_root:
        if args.command=='gates' and not args.gate_config:raise ValueError('External project gates require an explicit reviewed --gate-config')
        if args.command in ('candidate','compare','benchmark'):raise ValueError('Skill release management must target the engine repository')
    code=0
    new_commands={'skill-compatibility-audit','effective-policy-explainer','workflow-handoff-contract',
                  'skill-interference-benchmark','project-workflow-adapter','evidence-reconciler',
                  'memory-reconciliation','context-sufficiency-check'}
    if args.command in new_commands:
        from omega.io import read_json
        from omega.interop import compatibility,handoff,project_adapter
        from omega.analysis_tools import context_check,reconcile_evidence,reconcile_memory,interference
        document=read_json(ROOT,args.input) if args.input else None
        if args.command=='skill-compatibility-audit':result=compatibility(ROOT,args.skill_root,args.hook_config,document,CONFIG['limits']['max_agents'])
        elif args.command=='effective-policy-explainer':
            from omega.policy import explain
            result=explain(document,ROOT)
        elif args.command=='workflow-handoff-contract':result=handoff(ROOT,document,CONFIG['limits']['max_agents'])
        elif args.command=='skill-interference-benchmark':result=interference(document)
        elif args.command=='project-workflow-adapter':result=project_adapter(ROOT)
        elif args.command=='evidence-reconciler':result=reconcile_evidence(ROOT,args.evidence or ([args.record] if args.record else []),git,CONFIG)
        elif args.command=='memory-reconciliation':
            names=[args.record] if args.record else document.get('records',[]) if isinstance(document,dict) else []
            from omega.records import current_context
            result=reconcile_memory(ROOT,names,git('rev-parse','HEAD'),current_context(ROOT,git,CONFIG))
        else:result=context_check(ROOT,document)
        code=0 if result.get('passed',result.get('allowed',False)) else 1
    elif args.command=='context':
        from omega.context import packet
        result=packet(ROOT,args.select,args.max_bytes)
        if args.input:
            from omega.io import read_json
            task=read_json(ROOT,args.input)
            if not isinstance(task,dict):raise ValueError('Expected a task manifest')
            result['task']={k:task[k] for k in ('acceptance','constraints')}
            from omega.context import encode
            if len(encode(result).encode())>args.max_bytes:raise ValueError('Task packet exceeds byte budget')
    elif args.command=='doctor': result=doctor()
    elif args.command=='map': result=inventory()
    elif args.command=='plan':
        from omega.io import read_json
        doc=read_json(ROOT,args.input) if args.input else {}
        if not isinstance(doc,dict):raise ValueError('Expected a plan input object')
        result=plan(doc.get('complexity',args.complexity),doc.get('conflict',args.conflict),doc.get('intent','change'),doc.get('workflow'))
        code=1 if result['workflow_contract'] is not None and not result['workflow_contract']['passed'] else 0
    elif args.command=='audit':
        result=audit(args.select);code=0 if result['passed'] else 1
    elif args.command=='benchmark':
        if args.skill:
            from omega.skills import assess, suite_digest
            from omega.records import workspace, test_outcomes, execution_context
            assessment=assess(ROOT,args.skill,args.candidate)
            before=workspace(ROOT,git);execution=execution_context(ROOT,CONFIG)
            pattern='test_*.py'  # The unified skill must cover foundation and interoperability together.
            scenarios=run(['python3','-m','omega.test_runner','--start','tests','--pattern',pattern],CONFIG['limits']['max_gate_seconds'])
            result={'kind':'skill-evaluation','skill':args.skill,'assessment':assessment,
                    'candidate_sha256':assessment['sha256'],'candidate_bundle_sha256':assessment['bundle_sha256'],'suite_sha256':suite_digest(ROOT),
                    'workspace_sha256':before,'workspace_unchanged':before==workspace(ROOT,git),
                    'execution_fingerprint':execution['sha256'],'execution_unchanged':execution['sha256']==execution_context(ROOT,CONFIG)['sha256'],
                    'scenarios':scenarios,'test_outcomes':test_outcomes(scenarios),'native_quality':'UNVERIFIED'}
            result['passed']=assessment['passed'] and result['test_outcomes'] is not None and result['workspace_unchanged'] and result['execution_unchanged']
            result['evidence']=save('evidence',result)
        else:result=benchmark()
        code=0 if result['passed'] else 1
    elif args.command=='gates':
        result=gates();code=0 if result['passed'] else 1
        try:result['evidence']=save('evidence',result)
        except OSError as exc:
            # A read-only checkout still gets its gate results; only the reusable evidence record is lost.
            if exc.errno not in (errno.EROFS,errno.EACCES,errno.EPERM):raise
            result['evidence']=None
            result['evidence_unsaved']=f'Project is not writable ({exc.strerror}); results are shown but no evidence was persisted, so compare/change-check cannot reuse them'
        if args.summary:
            from omega.context import gate_summary
            result=gate_summary(result)
    elif args.command=='memory-read':
        from omega.records import memory_status,current_context
        if not args.record:raise ValueError('--record required')
        result=memory_status(ROOT,args.record,git('rev-parse','HEAD'),current_context(ROOT,git,CONFIG))
        code=1 if result['requires_validation'] else 0
    elif args.command=='change-plan':
        from omega.change import create
        result=create(ROOT,git,args.allow,args.acceptance,CONFIG['limits'],args.include_existing)
        result={'record':save('changes',result),**result}
    elif args.command=='change-check':
        from omega.change import check
        if not args.record:raise ValueError('--record required')
        from omega.records import execution_context
        result=check(ROOT,args.record,git,CONFIG['limits'],args.evidence,CONFIG['gates'],CONFIG.get('test_adapter','omega'),execution_context(ROOT,CONFIG)['sha256'],CONFIG.get('test_report'))
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
        payload=memory_payload(ROOT,args.title,args.body,args.select,args.evidence)
        if args.key:
            if not re.fullmatch('[a-z0-9][a-z0-9_.-]{0,63}',args.key):raise ValueError('Invalid decision key')
            payload['decision_key']=args.key
        result={'memory':save('memory',payload)}
    elif args.command=='isolate':
        if not args.name or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,60}',args.name): raise ValueError('Invalid branch name')
        if git('status','--porcelain'): raise ValueError('Dirty checkout: preserve changes before isolation')
        branch='omega/'+args.name
        if args.worktree:
            from omega.safety import artifact_path
            runtime_ready()
            p=artifact_path(ROOT,args.worktree,'worktrees',False)
            if p.exists():raise ValueError('Destination exists')
            result={'output':git('worktree','add','-b',branch,str(p),'HEAD')}
        else:result={'output':git('switch','-c',branch)}
    elif args.command=='rollback-check':
        result={'head':git('rev-parse','--verify','HEAD^{commit}'), 'diff_check':run(['git','diff','--check']),
                'strategy':'Review diff and use explicit approved revert commit. No automatic reset, clean, delete or revert.',
                'runtime_rollback':'not applicable: no deployed service or migration'}
        code=0 if result['diff_check']['exit_code']==0 else 1
    elif args.command=='candidate':
        from omega.skills import assess
        runtime_ready()
        result={'skill':args.skill,'sha256':fingerprint(args.skill),'skill_contract':assess(ROOT,args.skill),'benchmark':benchmark(),
                'promotion':'manual only; gates plus review required'}
        from omega.safety import artifact_path
        candidate = artifact_path(ROOT,'.omega/candidates/' + args.skill + '-' + uuid.uuid4().hex + '.md','candidates',False)
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_bytes(confined(f'.claude/skills/{args.skill}/SKILL.md').read_bytes())
        result['candidate'] = str(candidate.relative_to(ROOT))
        result['baseline']=save('baselines',result)
        code=0 if result['benchmark']['passed'] else 1
    else:
        if not args.baseline:raise ValueError('--baseline required')
        from omega.records import load, workspace, valid_gates, test_outcomes, execution_context
        from omega.skills import assess
        from omega.safety import artifact_path
        _,baseline=load(ROOT,args.baseline,'baselines')
        current=benchmark()
        same_suite=baseline['benchmark'].get('suite_sha256')==current['suite_sha256'] and baseline['benchmark']['suite']==current['suite'] and [x['id'] for x in baseline['benchmark']['cases']]==[x['id'] for x in current['cases']]
        candidate = artifact_path(ROOT,args.candidate or baseline['candidate'],'candidates')
        contract=assess(ROOT,baseline['skill'],str(candidate))
        stable_modified = baseline['sha256'] != fingerprint(baseline['skill'])
        stable_bundle_modified=baseline['skill_contract'].get('bundle_sha256')!=assess(ROOT,baseline['skill'])['bundle_sha256']
        passed=same_suite and not stable_modified and not stable_bundle_modified and baseline['benchmark']['passed'] and current['passed'] and contract['advanced_passed'] and contract['score']>=baseline['skill_contract']['score']
        gate_ok=False;scenario_ok=False;checks=[]
        for name in args.evidence:
            _,ev=load(ROOT,name,'evidence')
            fresh=ev.get('workspace_sha256')==workspace(ROOT,git) and ev.get('workspace_unchanged') is True and ev.get('head')==git('rev-parse','HEAD') and ev.get('passed') is True and ev.get('execution_fingerprint')==execution_context(ROOT,CONFIG)['sha256'] and ev.get('execution_unchanged') is True
            if ev.get('kind')=='skill-evaluation':
                valid=fresh and ev.get('skill')==baseline['skill'] and ev.get('candidate_sha256')==contract['sha256'] and ev.get('candidate_bundle_sha256')==contract['bundle_sha256'] and ev.get('suite_sha256')==current['suite_sha256'] and isinstance(ev.get('scenarios'),dict) and test_outcomes(ev['scenarios']) is not None
                scenario_ok=scenario_ok or valid
            else:
                valid=fresh and valid_gates(ev,CONFIG['gates'],CONFIG.get('test_adapter','omega'),CONFIG.get('test_report'))
                gate_ok=gate_ok or valid
            checks.append({'path':name,'valid':valid})
        passed=passed and all(x['valid'] for x in checks)
        result={'passed':passed,'skill':baseline['skill'],'before':baseline['sha256'],
                'after':hashlib.sha256(candidate.read_bytes()).hexdigest(),'benchmark':current,'stable_modified':stable_modified,
                'candidate_contract':contract,'baseline_contract':baseline['skill_contract'],'evidence_checks':checks,
                'eligible_for_review':passed and gate_ok and scenario_ok,'native_release_eligible':False,
                'review_scope':'offline contract and tooling only; native skill behavior unverified',
                'promotion':'not performed; human review required; native quality remains UNVERIFIED'}
        code=0 if passed else 1
    from omega.context import encode
    print(encode(result,args.compact))
    return code


def main():
    global ROOT, CONFIG
    previous_root,previous_config=ROOT,CONFIG
    try:return _dispatch()
    finally:ROOT,CONFIG=previous_root,previous_config


if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print(json.dumps({'error':str(exc)}),file=sys.stderr);sys.exit(2)
