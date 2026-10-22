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
HEADINGS=('Inputs','Workflow','Evidence','Failure handling','Stop conditions')


def assess(root,skill,candidate=None):
    if skill not in COMMANDS:raise ValueError('Unknown implemented skill')
    path=artifact_path(root,candidate,'candidates') if candidate else source_path(root,f'.claude/skills/{skill}/SKILL.md')
    if not path.is_file() or path.stat().st_size>8192:raise ValueError('Missing or oversized skill')
    raw=path.read_bytes();text=raw.decode('utf-8')
    fields={};valid=True
    if not text.startswith('---\n'):valid=False
    else:
        parts=text.split('---\n',2)
        if len(parts)!=3:valid=False
        else:
            for line in parts[1].splitlines():
                key,sep,value=line.partition(':')
                if not sep or key in fields or key not in ('name','description','disable-model-invocation'):
                    valid=False;continue
                fields[key]=value.strip()
    checks=[{'id':'frontmatter','passed':valid,'required':True},
            {'id':'identity','passed':fields.get('name')==skill,'required':True},
            {'id':'description','passed':bool(fields.get('description')),'required':True},
            {'id':'explicit-invocation','passed':fields.get('disable-model-invocation')=='true','required':True},
            {'id':'no-permission-bypass','passed':not any(x in text for x in ('--dangerously-skip-permissions','bypassPermissions','curl -k ')),'required':True}]
    for command in COMMANDS[skill]:
        checks.append({'id':'command:'+command,'passed':bool(re.search(r'python3 -m omega '+re.escape(command)+r'(?=[\s`]|$)',text)),'required':True})
    for heading in HEADINGS:
        checks.append({'id':'section:'+heading,'passed':bool(re.search(r'^## '+re.escape(heading)+r'\s*$',text,re.M)),'required':False})
    return {'skill':skill,'sha256':hashlib.sha256(raw).hexdigest(),'checks':checks,
            'passed':all(x['passed'] for x in checks if x['required']),
            'advanced_passed':all(x['passed'] for x in checks),
            'score':round(100*sum(x['passed'] for x in checks)/len(checks),2),
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
