"""Local evidence and memory validation; data never becomes executable policy."""
import hashlib
import json
import re
from pathlib import Path
from omega.safety import artifact_path, source_path


def load(root, name, kind):
    path=artifact_path(root,name,kind)
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('Duplicate artifact key')
            result[key]=value
        return result
    record=json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=unique)
    if not isinstance(record,dict) or type(record.get('schema')) is not int or record.get('schema')!=1 or record.get('project')!=str(Path(root).resolve()):
        raise ValueError('Artifact schema/project mismatch')
    return path,record


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(65536),b''):h.update(block)
    return h.hexdigest()


def workspace(root, git):
    names=[x for x in git('ls-files','-z','--cached','--others','--exclude-standard',raw=True).split('\0') if x]
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
        elif lexical.is_file():state={'sha256':digest(lexical)}
        elif not lexical.exists():state={'deleted':True}
        else:raise ValueError('Unsupported Git entry; inspect submodule or special file')
        entries.append([name,state])
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


def memory_status(root,name,head):
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
    for ref in record.get('evidence_refs',[]):
        try:
            path,_=load(root,ref['path'],'evidence')
            if digest(path)!=ref['sha256']:reasons.append('Evidence changed: '+ref['path'])
        except (OSError,ValueError):reasons.append('Evidence unavailable: '+ref['path'])
    return {'record':record,'stale':bool(reasons),'reasons':reasons,
            'verification':'references only; factual content and decisions require review',
            'legacy':record.get('kind')!='memory'}


def test_outcomes(result):
    """Use the runner's explicit counts, including when prefix capture was truncated."""
    if type(result.get('exit_code')) is not int or result['exit_code']!=0:return None
    text=result.get('output_tail') or result.get('output','')
    lines=[x[len('OMEGA_TEST_RESULT '):] for x in text.splitlines() if x.startswith('OMEGA_TEST_RESULT ')]
    if len(lines)!=1:return None
    try:counts=json.loads(lines[0])
    except (ValueError,TypeError):return None
    keys=('run','passed','failed','errors','skipped','expected_failures','unexpected_successes')
    if not isinstance(counts,dict) or any(type(counts.get(x)) is not int or counts[x]<0 for x in keys):return None
    if counts['run']!=sum(counts[x] for x in keys if x!='run') or counts['passed']<=0:return None
    if any(counts[x] for x in ('failed','errors','unexpected_successes')):return None
    return counts


def valid_gates(record,commands):
    rows=record.get('results')
    if record.get('kind')!='gates' or record.get('passed') is not True or not isinstance(rows,list) or len(rows)!=len(commands):return False
    if not all(isinstance(r,dict) and isinstance(r.get('gate'),str) and r.get('gate') in commands and r.get('command')==commands[r['gate']] and type(r.get('exit_code')) is int and r['exit_code']==0 for r in rows):return False
    if len({r['gate'] for r in rows})!=len(commands):return False
    tests=next((r for r in rows if r['gate']=='tests'),None)
    return tests is not None and test_outcomes(tests) is not None
