"""Read-only evidence, context, memory and imported A/B result analysis."""
from collections import defaultdict
import hashlib
from pathlib import Path
import re
import statistics
from omega.safety import source_path
from omega.records import load,digest,workspace,valid_gates,memory_status,execution_context


def context_check(root,document):
    if not isinstance(document,dict) or not isinstance(document.get('requirements'),dict) or not isinstance(document.get('packet'),dict):raise ValueError('Expected requirements and packet')
    req= document['requirements'];packet=document['packet'];issues=[]
    if not isinstance(packet.get('task'),dict):raise ValueError('Expected packet task invariants')
    for key in ('acceptance','constraints'):
        if not isinstance(req.get(key),list) or any(not isinstance(x,str) or not x.strip() for x in req[key]):raise ValueError('Invalid context task invariants')
        if key=='acceptance' and not req[key]:raise ValueError('Acceptance cannot be empty')
        if packet.get('task',{}).get(key)!=req[key]:issues.append('Task invariant missing/changed: '+key)
    required=req.get('sources');sources=packet.get('sources')
    if not isinstance(required,list) or not required or not isinstance(sources,list) or len(required)>128 or len(sources)>128:raise ValueError('Expected 1..128 required sources and bounded packet')
    actual=[]
    for source in sources:
        if not isinstance(source,dict) or not isinstance(source.get('path'),str):raise ValueError('Malformed context source')
        path=source_path(root,source['path'])
        if not path.is_file() or path.stat().st_size>1_000_000:raise ValueError('Missing or oversized context source')
        raw=path.read_bytes()
        if b'\x00' in raw:raise ValueError('Binary context source excluded')
        lines=raw.decode('utf-8').splitlines(keepends=True)
        start,end=source.get('start'),source.get('end')
        if type(start) is not int or type(end) is not int or not 1<=start<=end<=len(lines):raise ValueError('Invalid source range')
        if source.get('source_sha256')!=digest(path) or source.get('content')!=''.join(lines[start-1:end]):issues.append('Stale/altered source: '+source['path'])
        actual.append((str(path.relative_to(root)),start,end))
    for source in required:
        if not isinstance(source,dict) or not isinstance(source.get('path'),str):raise ValueError('Malformed source requirement')
        path=source_path(root,source['path']);start,end=source.get('start'),source.get('end')
        if type(start) is not int or type(end) is not int or not 1<=start<=end:raise ValueError('Invalid required range')
        if not any(name==str(path.relative_to(root)) and a<=start and b>=end for name,a,b in actual):issues.append('Missing required range: '+source['path'])
    return {'passed':not issues,'issues':issues,'required_ranges':len(required),'provided_ranges':len(actual),
            'scope':'explicit manifest only; cannot infer whether the caller listed every relevant dependency'}


def reconcile_evidence(root,names,git,config):
    if not names or len(names)>32:raise ValueError('Expected 1..32 evidence records')
    current=workspace(root,git);head=git('rev-parse','HEAD');runtime=execution_context(root,config)['sha256'];rows=[]
    for name in names:
        _,record=load(root,name,'evidence')
        verified=valid_gates(record,config['gates'],config.get('test_adapter','omega'))
        if not verified:state='not-successful-gate-evidence'
        elif record.get('workspace_sha256')!=current:state='stale-source'
        elif record.get('execution_fingerprint')!=runtime:state='stale-or-unbound-execution-context'
        elif record.get('head')!=head:state='same-source-different-head'
        else:state='current'
        rows.append({'record':name,'state':state,'requires_validation':state!='current'})
    return {'passed':all(x['state']=='current' for x in rows),'records':rows,
            'scope':'known local source/runtime fingerprint only; external platform policy remains unobserved'}


def reconcile_memory(root,names,head,context=None):
    if not names or len(names)>32:raise ValueError('Expected 1..32 explicit memory records')
    groups=defaultdict(list);stale=[]
    for name in names:
        result=memory_status(root,name,head,context);record=result['record'];key=record.get('decision_key') or record['title'].strip().casefold()
        if not isinstance(key,str) or not key.strip():raise ValueError('Invalid decision key')
        groups[key].append({'record':name,'body_sha256':hashlib.sha256(record['body'].encode()).hexdigest(),
                            'stale':result['stale'],'staleness':result.get('staleness','unknown')})
        if result['requires_validation']:stale.append(name)
    conflicts=[{'decision_key':key,'records':items,'action':'review alternatives; no automatic winner'} for key,items in groups.items() if len({x['body_sha256'] for x in items})>1]
    return {'passed':not conflicts and not stale,'conflicts':conflicts,'stale_records':stale,
            'groups':dict(groups),'files_written':False,'scope':'different wording is a review signal, not proof of logical contradiction'}


def interference(document):
    if not isinstance(document,dict) or not isinstance(document.get('runs'),list) or not 3<=len(document['runs'])<=600:raise ValueError('Expected 3..600 imported evaluation runs')
    records={};settings=set();criteria={};task_prompts={};provenances=set();bundles={}
    for run in document['runs']:
        if not isinstance(run,dict):raise ValueError('Malformed run')
        if not isinstance(run.get('task_id'),str) or not run['task_id'] or type(run.get('trial')) is not int or run['trial']<0:raise ValueError('Invalid task/trial')
        arm=run.get('arm')
        if arm not in ('A','B','A+B'):raise ValueError('Arm must be A, B or A+B')
        key=(run['task_id'],run['trial'],arm)
        if key in records:raise ValueError('Duplicate evaluation run')
        for name in ('model','model_version','grader_version','prompt_sha256'):
            if not isinstance(run.get(name),str) or not run[name]:raise ValueError('Missing evaluation identity')
        if not re.fullmatch('[0-9a-f]{64}',run['prompt_sha256']):raise ValueError('Invalid prompt digest')
        expected={'A','B'} if arm=='A+B' else {arm};declared=run.get('skill_bundles')
        if not isinstance(declared,dict) or set(declared)!=expected:raise ValueError('Declare exact skill bundle digests for each arm')
        for label,value in declared.items():
            if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):raise ValueError('Invalid skill bundle digest')
            if label in bundles and bundles[label]!=value:raise ValueError('Skill bundle changed across arms/trials')
            bundles[label]=value
        acceptance=run.get('acceptance')
        if not isinstance(acceptance,dict) or not acceptance or any(not isinstance(k,str) or type(v) is not bool for k,v in acceptance.items()):raise ValueError('Expected explicit boolean acceptance outcomes')
        task=run['task_id']
        if task not in criteria:criteria[task]=set(acceptance)
        if set(acceptance)!=criteria[task]:raise ValueError('Acceptance criteria must be held fixed per task')
        if task in task_prompts and task_prompts[task]!=run['prompt_sha256']:raise ValueError('Prompt changed across repeated task trials')
        task_prompts[task]=run['prompt_sha256']
        for name in ('tokens','duration_ms'):
            if run.get(name) is not None and (type(run[name]) is not int or not 0<=run[name]<=10**12):raise ValueError('Invalid usage measurement')
        if run.get('provenance') not in ('fixture','native','manual'):raise ValueError('Evaluation provenance required')
        provenances.add(run['provenance']);settings.add((run['model'],run['model_version'],run['grader_version']))
        records[key]=run
    if len(settings)!=1 or len(provenances)!=1:raise ValueError('Hold model/version, grader and provenance fixed')
    pairs=sorted({(task,trial) for task,trial,_ in records});regressions=[];summaries={}
    for task,trial in pairs:
        if any((task,trial,arm) not in records for arm in ('A','B','A+B')):raise ValueError('Unmatched evaluation arms')
        prompts={records[(task,trial,a)]['prompt_sha256'] for a in ('A','B','A+B')}
        if len(prompts)!=1:raise ValueError('Prompt changed across evaluation arms')
        passing={a:all(records[(task,trial,a)]['acceptance'].values()) for a in ('A','B','A+B')}
        if (passing['A'] or passing['B']) and not passing['A+B']:regressions.append({'task_id':task,'trial':trial})
    for arm in ('A','B','A+B'):
        rows=[r for (task,trial,a),r in records.items() if a==arm]
        summaries[arm]={'runs':len(rows),'accepted':sum(all(r['acceptance'].values()) for r in rows)}
        for field in ('tokens','duration_ms'):
            values=[r[field] for r in rows if r.get(field) is not None]
            summaries[arm][field+'_mean']=statistics.mean(values) if len(values)==len(rows) else None
    all_accepted=summaries['A+B']['accepted']==summaries['A+B']['runs']
    return {'analysis_valid':True,'passed':not regressions and all_accepted,'all_combined_acceptance_passed':all_accepted,'non_regression':not regressions,'regressions':regressions,'arms':summaries,
            'provenance':next(iter(provenances)),'skill_bundles':bundles,'grader_version':next(iter(settings))[2],'native_measurements_present':provenances=={'native'},
            'native_release_eligible':False,'scope':'imported outcomes, authenticity and semantic grading require independent review; no model requests sent'}
