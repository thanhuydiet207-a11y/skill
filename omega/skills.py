"""Versioned offline skill contracts; no claim to evaluate LLM reasoning."""
import hashlib
import re
from pathlib import Path
from omega.safety import source_path, artifact_path

COMMANDS={
    'repo-map':['map','plan'],
    'controlled-change':['isolate'],
    'quality-gates':['gates','rollback-check'],
    'project-memory':['memory'],
    'skill-benchmark':['candidate','compare','benchmark'],
}
import json
_EXTENSIONS=Path(__file__).resolve().parent/'extensions.json'
if _EXTENSIONS.is_file():
    extra=json.loads(_EXTENSIONS.read_text())
    if not isinstance(extra,dict) or any(not isinstance(k,str) or not isinstance(v,list) or any(not isinstance(x,str) for x in v) for k,v in extra.items()):raise ValueError('Invalid skill registry')
    COMMANDS.update(extra)
HEADINGS=('Inputs','Workflow','Evidence','Failure handling','Stop conditions')


def assess(root,skill,candidate=None):
    if skill not in COMMANDS:raise ValueError('Unknown implemented skill')
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
    resources=[]
    for name in sorted(set(re.findall(r'(?:docs|references|scripts|assets)/[A-Za-z0-9_./-]+\.(?:md|py|json|sh|txt)',body))):
        location=Path(root)/name if name.startswith('docs/') else Path(root)/'.claude/skills'/skill/name
        try:
            safe=source_path(root,str(location))
            if not safe.is_file() or safe.stat().st_size>1048576:raise ValueError('Missing or oversized resource')
            data=safe.read_bytes()
            resources.append({'path':str(safe.relative_to(root)),'sha256':hashlib.sha256(data).hexdigest(),'available':True})
        except (ValueError,OSError):resources.append({'path':name,'available':False})
    checks.append({'id':'resources-resolve','passed':all(x['available'] for x in resources),'required':True})
    bundle=hashlib.sha256(raw+__import__('json').dumps(resources,sort_keys=True).encode()).hexdigest()
    return {'skill':skill,'sha256':hashlib.sha256(raw).hexdigest(),'bundle_sha256':bundle,'resources':resources,'checks':checks,
            'passed':all(x['passed'] for x in checks if x['required']),
            'advanced_passed':all(x['passed'] for x in checks),
            'score':round(100*sum(x['passed'] for x in checks)/len(checks),2),
            'quality_score':None,'quality_evaluated':False,'score_metric':'contract completeness only',
            'scope':'offline document contract, not LLM instruction adherence or reasoning quality'}


def suite_digest(root):
    # Discover additions as well as edits: a new test/module must invalidate a baseline.
    root=Path(root).resolve();h=hashlib.sha256()
    for folder in ('omega','tests','benchmarks'):
        h.update(folder.encode()+b'\0')
        paths=sorted(p for p in (root/folder).rglob('*') if p.is_file() and p.suffix in ('.py','.json') and '__pycache__' not in p.parts)
        for path in paths:
            name=str(path.relative_to(root));verified=source_path(root,name)
            h.update(name.encode()+b'\0'+verified.read_bytes()+b'\0')
    return h.hexdigest()
