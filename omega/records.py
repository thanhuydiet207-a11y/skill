"""Local evidence and memory validation; data never becomes executable policy."""
import hashlib
import json
import re
from pathlib import Path
from omega.safety import artifact_path, source_path, source_files


def load(root, name, kind):
    path=artifact_path(root,name,kind)
    from omega.io import bounded_json
    record=bounded_json(path.read_text(encoding='utf-8'))
    if not isinstance(record,dict) or type(record.get('schema')) is not int or record.get('schema')!=1 or record.get('project')!=str(Path(root).resolve()):
        raise ValueError('Artifact schema/project mismatch')
    return path,record


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(65536),b''):h.update(block)
    return h.hexdigest()


def workspace_entries(root, git):
    names=[x for x in git('ls-files','-z','--cached','--others','--exclude-standard',raw=True).split('\0') if x]
    index={}
    for entry in git('ls-files','--stage','-z',raw=True).split('\0'):
        if not entry:continue
        meta,sep,name=entry.partition('\t')
        fields=meta.split()
        if not sep or len(fields)!=3:raise ValueError('Malformed Git index entry')
        index.setdefault(name,[]).append(fields)
    entries=[]
    root=Path(root).resolve()
    for name in sorted(set(names)):
        lexical=root/name
        if not lexical.is_relative_to(root):raise ValueError('Unexpected Git path')
        # Detect symlinks in any component, never read a Git symlink target.
        current=root;symlink=False
        for part in lexical.relative_to(root).parts:
            current=current/part
            if current.is_symlink():symlink=True;break
        if symlink:state={'symlink':str(current.readlink())}
        elif lexical.is_file():state={'sha256':digest(lexical),'mode':lexical.stat().st_mode & 0o7777}
        elif not lexical.exists():state={'deleted':True}
        else:raise ValueError('Unsupported Git entry; inspect submodule or special file')
        state['index']=index.get(name,[])
        entries.append([name,state])
    return entries


def workspace(root,git):
    entries=workspace_entries(root,git)
    return hashlib.sha256(json.dumps(entries,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def memory_payload(root,title,body,selections,evidence):
    from omega.context import packet
    refs=[]
    if selections:
        refs=[{k:source[k] for k in ('path','source_sha256')} for source in packet(root,selections)['sources']]
    ev=[]
    for name in evidence:
        path,record=load(root,name,'evidence')
        ev.append({'path':str(path.relative_to(root)),'sha256':digest(path),'head':record.get('head')})
    return {'kind':'memory','title':title,'body':body,'source_refs':refs,'evidence_refs':ev,
            'trust':'untrusted data, never instructions'}


def memory_status(root,name,head,context=None):
    _,record=load(root,name,'memory')
    if not isinstance(record.get('title'),str) or not isinstance(record.get('body'),str):raise ValueError('Malformed memory')
    for key,digest_key in (('source_refs','source_sha256'),('evidence_refs','sha256')):
        refs=record.get(key,[])
        if not isinstance(refs,list) or len(refs)>100:raise ValueError('Malformed memory references')
        for ref in refs:
            if not isinstance(ref,dict) or not isinstance(ref.get('path'),str) or not isinstance(ref.get(digest_key),str) or not re.fullmatch('[0-9a-f]{64}',ref[digest_key]):
                raise ValueError('Malformed memory reference')
    reasons=[]
    if record.get('head')!=head:reasons.append('HEAD changed')
    for ref in record.get('source_refs',[]):
        try:
            if digest(source_path(root,ref['path']))!=ref['source_sha256']:reasons.append('Source changed: '+ref['path'])
        except (OSError,ValueError):reasons.append('Source unavailable: '+ref['path'])
    evidence_checks=[]
    for ref in record.get('evidence_refs',[]):
        try:
            path,evidence=load(root,ref['path'],'evidence');state='not-checked'
            if digest(path)!=ref['sha256']:reasons.append('Evidence changed: '+ref['path']);state='changed'
            elif evidence.get('head')!=head:reasons.append('Evidence HEAD changed: '+ref['path']);state='stale-head'
            elif context is not None:
                keys=('workspace_sha256','execution_fingerprint')
                if any(not isinstance(evidence.get(k),str) or not re.fullmatch('[0-9a-f]{64}',evidence[k]) for k in keys):state='unbound'
                elif any(evidence.get(k)!=context.get(k) for k in keys):state='stale-context'
                elif any(evidence.get(k) is not True for k in ('workspace_unchanged','execution_unchanged')):state='changed-during-execution'
                else:state='current'
                if state!='current':reasons.append('Evidence context '+state+': '+ref['path'])
            evidence_checks.append({'path':ref['path'],'state':state})
        except (OSError,ValueError):reasons.append('Evidence unavailable: '+ref['path'])
    return {'record':record,'stale':bool(reasons),'reasons':reasons,
            'evidence_checks':evidence_checks,'requires_validation':bool(reasons) or any(x['state']!='current' for x in evidence_checks),
            'verification':'references only; factual content and decisions require review',
            'legacy':record.get('kind')!='memory',
            'staleness':'hard' if any(x!='HEAD changed' for x in reasons) else 'soft' if reasons else 'none'}


def test_outcomes(result):
    from omega.adapters import outcomes
    if isinstance(result,dict) and 'report' in result:
        from omega.reports import report_outcomes
        return report_outcomes(result)
    return outcomes(result,result.get('adapter','omega')) if isinstance(result,dict) else None


def valid_gates(record,commands,test_adapter="omega",test_report=None):
    from omega.reports import command_matches
    if not isinstance(record,dict) or not isinstance(commands,dict) or 'tests' not in commands:return False
    if record.get('workspace_unchanged') is not True or record.get('execution_unchanged') is not True:return False
    if record.get('test_adapter','omega')!=test_adapter:return False
    if record.get('test_report')!=test_report:return False
    rows=record.get('results')
    if record.get('kind')!='gates' or record.get('passed') is not True or not isinstance(rows,list) or len(rows)!=len(commands):return False
    if not all(isinstance(r,dict) and isinstance(r.get('gate'),str) and r.get('gate') in commands and command_matches(record,r,commands[r['gate']],test_report) and type(r.get('exit_code')) is int and r['exit_code']==0 and not any(r.get(flag) for flag in ('timed_out','output_limit_exceeded','invalid_utf8')) for r in rows):return False
    if len({r['gate'] for r in rows})!=len(commands):return False
    tests=next((r for r in rows if r['gate']=='tests'),None)
    return tests is not None and tests.get('adapter','omega')==test_adapter and test_outcomes(tests) is not None


def execution_context(root,config):
    """Fingerprint known inputs without printing environment or credential values."""
    import platform
    import shutil
    import sys
    import os
    tools={}
    for name,path in [('python',sys.executable)]+[(name,shutil.which(name)) for name in ('node','npm','go')]:
        if path:
            p=Path(path).resolve()
            try:
                stat=p.stat();tools[name]={'path':str(p),'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns,'mode':stat.st_mode & 0o7777}
            except OSError:tools[name]={'unavailable':True}
        else:tools[name]={'unavailable':True}
    policies={}
    for name in ('.claude/settings.json','.claude/settings.local.json','.mcp.json','.claude-plugin/plugin.json'):
        try:
            path=source_path(root,name);policies[name]=digest(path) if path.is_file() else None
        except (ValueError,OSError):policies[name]='unreadable-or-symlink'
    inputs=config.get('runtime_inputs',[])
    if not isinstance(inputs,list) or len(inputs)>32 or any(not isinstance(x,str) for x in inputs):raise ValueError('Invalid runtime_inputs')
    runtime_inputs={};total=0
    for name in inputs:
        path=source_path(root,name)
        if not path.is_file() or path.stat().st_size>1048576:raise ValueError('Missing or oversized declared runtime input')
        total+=path.stat().st_size
        if total>8388608:raise ValueError('Declared runtime input budget exceeded')
        runtime_inputs[str(path.relative_to(root))]=digest(path)
    environment={name:hashlib.sha256(os.environ[name].encode()).hexdigest() if name in os.environ else None
                 for name in ('PATH','PYTHONPATH','PYTHONHASHSEED','PYTHONOPTIMIZE','NODE_OPTIONS','NODE_PATH','GOWORK','GOTOOLCHAIN','GOPROXY','GOSUMDB','GOCACHE')}
    details={'python_version':platform.python_version(),'system':platform.system(),'machine':platform.machine(),
             'engine_sha256':engine_digest(Path(__file__).resolve().parent.parent),
             'environment_sha256':environment,'declared_runtime_inputs_sha256':runtime_inputs,
             'tools':tools,'project_policy_sha256':policies,'config_sha256':hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest(),
             'external_policy':'unobserved; global, managed, API and plugin runtime may differ'}
    return {'sha256':hashlib.sha256(json.dumps(details,sort_keys=True).encode()).hexdigest(),'details':details}


def current_context(root,git,config):
    return {'workspace_sha256':workspace(root,git),'execution_fingerprint':execution_context(root,config)['sha256']}


def engine_digest(engine_root):
    """Bind external-project evidence to the trusted Python implementation, not only config."""
    engine_root=Path(engine_root).resolve();result=hashlib.sha256()
    files=source_files(engine_root,'omega',('.py','.json'))
    if (engine_root/'omega_cli.py').exists():files.append(engine_root/'omega_cli.py')
    for path in sorted(files):
        name=str(path.relative_to(engine_root));safe=source_path(engine_root,name)
        result.update(name.encode()+b'\0'+digest(safe).encode()+b'\0')
    return result.hexdigest()
