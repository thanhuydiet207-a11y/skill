"""Versioned offline skill contracts; no claim to evaluate LLM reasoning."""
import hashlib
import json
import re
from pathlib import Path
from omega.safety import source_path, artifact_path, source_files

COMMANDS={'omega':['doctor','map','plan']}
MODES=json.loads((Path(__file__).resolve().parent/'modes.json').read_text())
if not isinstance(MODES,dict) or len(MODES)!=13:raise ValueError('Invalid OMEGA mode registry')
for name,mode in MODES.items():
    if not re.fullmatch('[a-z0-9][a-z0-9-]{0,63}',name) or not isinstance(mode,dict) or set(mode)!={'commands','reference'}:
        raise ValueError('Invalid OMEGA mode')
    if mode['reference']!=f'references/{name}.md' or not isinstance(mode['commands'],list) or not mode['commands'] or any(not isinstance(x,str) or not re.fullmatch('[a-z][a-z-]*',x) for x in mode['commands']):
        raise ValueError('Invalid OMEGA mode commands/reference')
HEADINGS=('Inputs','Workflow','Evidence','Failure handling','Stop conditions')
RESOURCE_PATTERN=r'(?:docs|references|scripts|assets)/[A-Za-z0-9_./-]+\.(?:md|py|json|sh|txt)'


def resources_for(root,skill,body):
    """Bound transitive local references for freshness, without executing their contents."""
    pending=set(re.findall(RESOURCE_PATTERN,body));seen=set();resources=[];texts={};total=0
    while pending:
        name=min(pending);pending.remove(name)
        if name in seen:continue
        seen.add(name)
        if len(seen)>64:raise ValueError('Skill resource count budget exceeded')
        location=Path(root)/name if name.startswith('docs/') else Path(root)/'.claude/skills'/skill/name
        try:
            safe=source_path(root,str(location))
            if not safe.is_file() or safe.stat().st_size>1048576:raise ValueError('Missing or oversized resource')
            with safe.open('rb') as stream:data=stream.read(1048577)
            if len(data)>1048576:raise ValueError('Oversized resource')
            total+=len(data)
            if total>1048576:raise OverflowError('Skill resource byte budget exceeded')
            if safe.suffix=='.md':
                text=data.decode('utf-8');texts[name]=text
                pending.update(set(re.findall(RESOURCE_PATTERN,text))-seen)
            resources.append({'path':str(safe.relative_to(root)),'sha256':hashlib.sha256(data).hexdigest(),'available':True})
        except OverflowError as exc:raise ValueError(str(exc)) from exc
        except (ValueError,OSError):resources.append({'path':name,'available':False})
    return sorted(resources,key=lambda x:x['path']),texts


def assess(root,skill,candidate=None):
    if skill not in COMMANDS:raise ValueError('Only unified skill omega is registered; use --skill omega')
    path=artifact_path(root,candidate,'candidates') if candidate else source_path(root,f'.claude/skills/{skill}/SKILL.md')
    if not path.is_file() or path.stat().st_size>8192:raise ValueError('Missing or oversized skill')
    from omega.frontmatter import parse
    raw=path.read_bytes();text=raw.decode('utf-8');document=parse(text)
    fields=document['fields'];valid=document['supported'] and not document['unknown_fields']
    checks=[{'id':'frontmatter','passed':valid,'required':True},
            {'id':'identity','passed':fields.get('name')==skill,'required':True},
            {'id':'description','passed':isinstance(fields.get('description'),str) and bool(fields.get('description','').strip()),'required':True},
            {'id':'explicit-invocation','passed':fields.get('disable-model-invocation') is True,'required':True},
            {'id':'no-permission-bypass','passed':not any(x in text for x in ('--dangerously-skip-permissions','bypassPermissions','curl -k ')),'required':True}]
    for command in COMMANDS[skill]:
        checks.append({'id':'command:'+command,'passed':bool(re.search(r'python3 -m omega '+re.escape(command)+r'(?=[\s`]|$)',text)),'required':True})
    body=document['body']
    for heading in HEADINGS:
        match=re.search(r'^## '+re.escape(heading)+r'\s*\n(.*?)(?=^## |\Z)',body,re.M|re.S)
        section=match[1].strip() if match else ''
        nonempty=len(section)>=24 and len(section.split())>=4
        checks.append({'id':'section:'+heading,'passed':nonempty,'required':False})
    resources,texts=resources_for(root,skill,body)
    modes=[]
    direct=set(re.findall(RESOURCE_PATTERN,body))
    for name,mode in MODES.items():
        text=texts.get(mode['reference'],'')
        commands=all(re.search(r'python3 -m omega '+re.escape(command)+r'(?=[\s`]|$)',text) for command in mode['commands'])
        safe=not any(x in text for x in ('--dangerously-skip-permissions','bypassPermissions','curl -k '))
        passed=mode['reference'] in direct and bool(text) and commands and safe
        modes.append({'id':name,'reference':mode['reference'],'passed':passed})
        checks.append({'id':'mode:'+name,'passed':passed,'required':True})
    checks.append({'id':'resources-resolve','passed':all(x['available'] for x in resources),'required':True})
    bundle=hashlib.sha256(raw+__import__('json').dumps(resources,sort_keys=True).encode()).hexdigest()
    return {'skill':skill,'sha256':hashlib.sha256(raw).hexdigest(),'bundle_sha256':bundle,'resources':resources,'modes':modes,'checks':checks,
            'passed':all(x['passed'] for x in checks if x['required']),
            'advanced_passed':all(x['passed'] for x in checks),
            'score':round(100*sum(x['passed'] for x in checks)/len(checks),2),
            'quality_score':None,'quality_evaluated':False,'score_metric':'contract completeness only',
            'scope':'offline document contract, not LLM instruction adherence or reasoning quality'}


def suite_digest(root):
    # Discover additions as well as edits: a new test/module must invalidate a baseline.
    root=Path(root).resolve();h=hashlib.sha256()
    for folder in ('omega','tests','benchmarks','integration/typescript','.claude-plugin','agents'):
        h.update(folder.encode()+b'\0')
        paths=source_files(root,folder,('.py','.json','.ts','.mjs','.md'))
        for path in paths:
            name=str(path.relative_to(root));verified=source_path(root,name)
            h.update(name.encode()+b'\0'+verified.read_bytes()+b'\0')
    return h.hexdigest()
