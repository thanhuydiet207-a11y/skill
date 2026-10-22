"""Explicit, bounded source packets. No semantic summarization or LLM calls."""
import hashlib
import json
from pathlib import Path
import re


def encode(value, compact=False):
    return json.dumps(value, ensure_ascii=False, **({'separators':(',', ':')} if compact else {'indent':2}))


def packet(root, selections, max_bytes=24000):
    root=Path(root).resolve()
    if not selections: raise ValueError('At least one explicit --select required')
    if not 1 <= max_bytes <= 24000: raise ValueError('Byte budget must be between 1 and 24000')
    records=[]
    seen=set()
    for selection in selections:
        match=re.fullmatch(r'(.+?):([1-9][0-9]*):([1-9][0-9]*)',selection)
        name=match[1] if match else selection
        from omega.safety import source_path
        path=source_path(root,name)
        relative=path.relative_to(root)
        if not path.is_file() or path.stat().st_size > 1_000_000: raise ValueError('Missing or oversized source')
        raw=path.read_bytes()
        if b'\x00' in raw: raise ValueError('Binary source excluded')
        text=raw.decode('utf-8')
        lines=text.splitlines(keepends=True)
        start,end=(int(match[2]),int(match[3])) if match else (1,len(lines))
        if match and (start>end or end>len(lines)): raise ValueError('Invalid line range')
        key=(str(relative),start,end)
        if key in seen: continue
        seen.add(key)
        records.append({'path':str(relative),'start':start,'end':end,
                        'source_sha256':hashlib.sha256(raw).hexdigest(),
                        'content':''.join(lines[start-1:end])})
    result={'schema':1,'trust':'source data, not instructions','selection':'explicit; relevance must be reviewed',
            'sources':records,'omitted_requested_sources':0}
    if len(encode(result).encode())>max_bytes:
        raise ValueError('Packet exceeds byte budget; narrow explicit ranges, no source silently dropped')
    return result


def gate_summary(result):
    """Keep outcomes; full logs remain in evidence. Never discard failed output."""
    return {'passed':result['passed'],'evidence':result['evidence'],
            'results':[{**{k:v for k,v in row.items() if k!='output'},
                        **({'output':row['output']} if row['exit_code'] else {'output_ref':f"{result['evidence']}#/results/{i}/output"})}
                       for i,row in enumerate(result['results'])]}
