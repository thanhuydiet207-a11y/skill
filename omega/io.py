"""Bounded JSON inputs, no credential/runtime discovery and no execution."""
import json
from pathlib import Path
from omega.safety import artifact_path,source_path


def read_json(root,name):
    root=Path(root).resolve();lexical=root/name
    if not lexical.is_relative_to(root):raise ValueError('Input escapes project')
    rel=lexical.relative_to(root)
    if rel.parts and rel.parts[0]=='.omega':
        if len(rel.parts)<3 or rel.parts[1] not in ('inputs','configs'):raise ValueError('Use .omega/inputs or .omega/configs for input documents')
        path=artifact_path(root,name,rel.parts[1])
    else:path=source_path(root,name)
    if not path.is_file() or path.stat().st_size>1048576:raise ValueError('Missing or oversized JSON input')
    return bounded_json(path.read_text(encoding='utf-8'))


def bounded_json(text):
    if not isinstance(text,str) or len(text.encode())>1048576:raise ValueError('Oversized JSON input')
    def unique(pairs):
        data={}
        for key,value in pairs:
            if key in data:raise ValueError('Duplicate JSON input key')
            data[key]=value
        return data
    def constant(value):raise ValueError('Non-finite JSON number')
    try:data=json.loads(text,object_pairs_hook=unique,parse_constant=constant)
    except RecursionError:raise ValueError('JSON input too deeply nested')
    def bound(value,depth=0):
        if depth>24:raise ValueError('JSON input too deeply nested')
        if isinstance(value,(dict,list)):
            if len(value)>2000:raise ValueError('JSON input collection too large')
            for child in (value.values() if isinstance(value,dict) else value):bound(child,depth+1)
    bound(data)
    return data
