"""Explicit scope and finite repair ledger for one isolated change."""
import fcntl
import json
import os
from pathlib import Path
import re
import time
from omega.records import load, workspace
from omega.safety import source_path


def create(root,git,allowed,acceptance,limits):
    if git('status','--porcelain'):raise ValueError('Change plan requires a clean checkout')
    if git('branch','--show-current') in ('','main','master'):raise ValueError('Create an isolated branch first')
    if not allowed or not acceptance:raise ValueError('Explicit --allow paths and --acceptance required')
    if any(not isinstance(x,str) or not x.strip() or len(x)>2000 for x in acceptance):raise ValueError('Invalid acceptance')
    paths=sorted({str(source_path(root,x).relative_to(root)) for x in allowed})
    maximum=limits['max_repair_attempts'];seconds=limits['max_task_seconds']
    if type(maximum) is not int or not 1<=maximum<=5 or type(seconds) is not int or not 1<=seconds<=1800:
        raise ValueError('Invalid repair/time limits')
    now=time.time()
    return {'kind':'change-plan','base_head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),
            'allowed_paths':paths,'acceptance':acceptance,'attempts':[],
            'max_attempts':maximum,'opened_at':now,'deadline':now+seconds,
            'rollback':'Review explicit revert against base_head; no automatic destructive rollback'}


def validate(record,limits):
    if record.get('kind')!='change-plan' or not isinstance(record.get('attempts'),list):raise ValueError('Malformed change plan')
    if not isinstance(record.get('allowed_paths'),list) or not record['allowed_paths'] or any(not isinstance(x,str) or not x for x in record['allowed_paths']):raise ValueError('Missing scope')
    if type(record.get('max_attempts')) is not int or not 1<=record['max_attempts']<=limits['max_repair_attempts']:
        raise ValueError('Invalid attempt limit')
    opened=record.get('opened_at');deadline=record.get('deadline')
    if not isinstance(opened,(int,float)) or not isinstance(deadline,(int,float)) or not 0<deadline-opened<=limits['max_task_seconds']:
        raise ValueError('Invalid task deadline')
    return opened<=time.time()<=deadline


def check(root,name,git,limits,evidence=(),gate_commands=None,test_adapter="omega"):
    _,record=load(root,name,'changes')
    active=validate(record,limits)
    names=git('diff','--no-renames','--name-only','-z','HEAD',raw=True).split('\0')
    names+=git('ls-files','--others','--exclude-standard','-z',raw=True).split('\0')
    changed=sorted(set(x for x in names if x))
    outside=[]
    for path in changed:
        try:resolved=str(source_path(root,path).relative_to(root))
        except (ValueError,OSError):outside.append(path);continue
        if resolved not in record['allowed_paths']:outside.append(path)
    same_head=record['base_head']==git('rev-parse','HEAD')
    same_branch=record['branch']==git('branch','--show-current')
    from omega.records import valid_gates
    if evidence and gate_commands is None:raise ValueError('Gate policy required to verify evidence')
    checks=[]
    for name in evidence:
        _,ev=load(root,name,'evidence')
        checks.append({'path':name,'passed':valid_gates(ev,gate_commands,test_adapter) and ev.get('workspace_unchanged') is True and
                       ev.get('workspace_sha256')==workspace(root,git) and ev.get('head')==record['base_head']})
    return {'passed':not outside and active and same_head and same_branch and all(x['passed'] for x in checks),
            'changed_paths':changed,'outside_scope':outside,'active':active,
            'base_head_matches':same_head,'branch_matches':same_branch,'acceptance':record['acceptance'],
            'gate_evidence':checks,'acceptance_verified':'human review required; strings are not assertions'}


def attempt(root,name,reason,limits):
    if not reason or len(reason)>500 or re.search(r'(?i)(secret|token|password)\s*[:=]',reason):raise ValueError('Invalid/sensitive repair reason')
    path,_=load(root,name,'changes')
    # Lock the same inode; no replace-under-lock race. This is a cooperative local ledger,
    # not authorization against an actor who can edit repository state directly.
    with path.open('r+',encoding='utf-8') as stream:
        try:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('Repair ledger busy; retry after current operation')
        record=json.load(stream)
        if not validate(record,limits):raise ValueError('Task deadline exceeded')
        if len(record['attempts'])>=record['max_attempts']:raise ValueError('Repair budget exhausted')
        record['attempts'].append({'number':len(record['attempts'])+1,'reason':reason,'at':time.time()})
        stream.seek(0);stream.write(json.dumps(record,indent=2,ensure_ascii=False)+'\n');stream.truncate();stream.flush();os.fsync(stream.fileno())
    return {'attempt':len(record['attempts']),'remaining':record['max_attempts']-len(record['attempts']),
            'deadline':record['deadline']}
