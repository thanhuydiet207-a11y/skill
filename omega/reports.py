"""Per-run structured test reports. No reuse, cleanup or execution of report contents."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import uuid
from omega.safety import artifact_path

LIMIT=262144
TOKEN='{report_path}'
TEMPLATE=r'\.omega/reports/\{run_id\}/[A-Za-z0-9][A-Za-z0-9_.-]{0,63}'


def validate_policy(config):
    template=config.get('test_report');commands=config['gates']
    mentions=[(name,i) for name,argv in commands.items() for i,arg in enumerate(argv) if TOKEN in arg]
    if template is None:
        if mentions:raise ValueError('report_path placeholder requires test_report policy')
        return
    if not isinstance(template,str) or not re.fullmatch(TEMPLATE,template):raise ValueError('test_report must use .omega/reports/{run_id}/FILENAME')
    if config.get('test_adapter') not in ('jest','junit'):raise ValueError('File reports support jest or junit only')
    if len(mentions)!=1 or mentions[0][0]!='tests' or mentions[0][1]==0 or sum(arg.count(TOKEN) for arg in commands['tests'])!=1:
        raise ValueError('Use exactly one report_path placeholder in test arguments, never executable or other gates')


def materialize(root,config):
    validate_policy(config);commands={name:list(argv) for name,argv in config['gates'].items()}
    if config.get('test_report') is None:return commands,None
    name=config['test_report'].replace('{run_id}',uuid.uuid4().hex)
    path=artifact_path(root,name,'reports',False)
    path.parent.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    path.parent.mkdir(mode=0o700,exist_ok=False)
    commands['tests']=[arg.replace(TOKEN,str(path)) for arg in commands['tests']]
    return commands,{'path':name,'adapter':config['test_adapter'],'fresh_namespace':True}


def read_report(root,spec):
    if spec.get('fresh_namespace') is not True:raise ValueError('Unbound report namespace')
    path=artifact_path(root,spec['path'],'reports')
    def identity(info):return [info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns,info.st_nlink]
    descriptor=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(descriptor,'rb') as stream:
        before=os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or before.st_size>LIMIT:raise ValueError('Report must be a bounded regular file with one link')
        raw=stream.read(LIMIT+1);after=os.fstat(stream.fileno())
        if len(raw)>LIMIT or identity(before)!=identity(after):raise ValueError('Report changed while reading or exceeded budget')
    content=raw.decode('utf-8')
    if b'\0' in raw or len(json.dumps(content,ensure_ascii=False).encode())>524288:raise ValueError('Report exceeds safe evidence encoding budget')
    return {**spec,'fresh':True,'unchanged':True,'sha256':hashlib.sha256(raw).hexdigest(),
            'bytes':len(raw),'identity':identity(after),'content':content}


def still_unchanged(root,report):
    try:
        current=read_report(root,report)
        return current['sha256']==report['sha256'] and current['identity']==report['identity']
    except (ValueError,OSError):return False


def report_outcomes(row):
    from omega.adapters import outcomes
    report=row.get('report')
    if not isinstance(report,dict) or any(report.get(key) is not True for key in ('fresh_namespace','fresh','unchanged')):return None
    content=report.get('content')
    if not isinstance(content,str) or len(content.encode())>LIMIT or report.get('adapter')!=row.get('adapter'):return None
    raw=content.encode()
    if type(report.get('bytes')) is not int or report['bytes']!=len(raw) or hashlib.sha256(raw).hexdigest()!=report.get('sha256'):return None
    return outcomes({**row,'output':content,'output_tail':'','truncated':False},row['adapter'])


def command_matches(record,row,configured,template):
    if template is None:return 'report' not in row and row.get('command')==configured
    if not isinstance(template,str) or not re.fullmatch(TEMPLATE,template):return False
    if row.get('gate')!='tests':return 'report' not in row and row.get('command')==configured
    report=row.get('report');root=record.get('project')
    if not isinstance(report,dict) or not isinstance(root,str) or not Path(root).is_absolute():return False
    path=report.get('path')
    pattern=re.escape(template).replace(re.escape('{run_id}'),'[0-9a-f]{32}')
    if not isinstance(path,str) or not re.fullmatch(pattern,path):return False
    try:resolved=artifact_path(root,path,'reports',False)
    except (ValueError,OSError):return False
    return row.get('configured_command')==configured and row.get('command')==[arg.replace(TOKEN,str(resolved)) for arg in configured]
