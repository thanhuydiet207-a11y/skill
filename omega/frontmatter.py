"""Safe subset of YAML frontmatter, never executes tags/anchors or embedded hooks.
Unsupported syntax is reported for manual review, not called natively invalid.
"""
import json
import re

KNOWN={'name','description','disable-model-invocation','user-invocable','allowed-tools','context','agent',
       'model','effort','hooks','license','metadata','compatibility','argument-hint'}


def scalar(value):
    value=value.strip()
    if not value:return ''
    if value in ('true','false'):return value=='true'
    if value.startswith('"'):
        try:return json.loads(value)
        except ValueError:raise ValueError('Unsupported quoted YAML scalar')
    if value.startswith("'") and value.endswith("'"):return value[1:-1].replace("''", "'")
    if value.startswith('[') or value.startswith('{'):
        try:return json.loads(value)
        except ValueError:raise ValueError('Flow YAML must use JSON quoting in this validator')
    if value[0] in '&*!' or '<<:' in value:raise ValueError('YAML tags, anchors and merges require manual review')
    return value


def parse(text):
    result={'fields':{},'body':'','supported':False,'errors':[],'unknown_fields':[]}
    lines=text.splitlines()
    if not lines or lines[0]!='---':result['errors']=['Missing frontmatter'];return result
    try:end=lines.index('---',1)
    except ValueError:result['errors']=['Unterminated frontmatter'];return result
    result['body']='\n'.join(lines[end+1:]);fields=result['fields'];i=1
    try:
        while i<end:
            line=lines[i];i+=1
            if not line.strip() or line.lstrip().startswith('#'):continue
            match=re.fullmatch(r'([A-Za-z][A-Za-z0-9_-]*):(?:\s+(.*))?',line)
            if not match:raise ValueError('Unsupported YAML structure')
            key,value=match[1],match[2] or ''
            if key in fields:raise ValueError('Duplicate frontmatter key')
            if key not in KNOWN:result['unknown_fields'].append(key)
            if value in ('|','>'):
                block=[]
                while i<end and (lines[i].startswith((' ','\t')) or not lines[i].strip()):block.append(lines[i].strip());i+=1
                fields[key]=('\n' if value=='|' else ' ').join(block)
            elif not value and i<end and lines[i].startswith('  '):
                nested={}
                while i<end and lines[i].startswith('  '):
                    sub=re.fullmatch(r'  ([A-Za-z][A-Za-z0-9_-]*):\s*(.*)',lines[i]);i+=1
                    if not sub or sub[1] in nested:raise ValueError('Unsupported or duplicate nested metadata')
                    nested[sub[1]]=scalar(sub[2])
                fields[key]=nested
            else:fields[key]=scalar(value)
        result['supported']=True
    except ValueError as exc:result['errors'].append(str(exc))
    return result
