"""Measure exact UTF-8 bytes, NOT model token counts or LLM answer quality."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from omega.context import encode, packet, gate_summary
from omega.__main__ import plan


def measurement(name, before, after, equivalent):
    a,b=len(before.encode()),len(after.encode())
    return {'case':name,'before_utf8_bytes':a,'after_utf8_bytes':b,
            'reduction_percent':round((a-b)*100/a,2),'data_equivalent':equivalent}


def main():
    cases=[]
    for complexity in ('low','medium','high'):
        value=plan(complexity,complexity=='high')
        before,after=encode(value),encode(value,True)
        cases.append(measurement('plan-'+complexity,before,after,json.loads(before)==json.loads(after)))
    value=packet(ROOT,['omega/context.py:1:20','omega/context.py:1:20'])
    before,after=encode(value),encode(value,True)
    cases.append(measurement('explicit-source-packet',before,after,json.loads(before)==json.loads(after)))
    proc=subprocess.run([sys.executable,'-m','omega','gates'],cwd=ROOT,capture_output=True,text=True,timeout=600)
    if proc.returncode:raise RuntimeError('Required gates failed: '+proc.stdout+proc.stderr)
    full=json.loads(proc.stdout)
    summary=gate_summary(full)
    restored=copy.deepcopy(summary)
    artifact=json.loads((ROOT/full['evidence']).read_text())
    for i,row in enumerate(restored['results']):
        for key in ('output','output_tail'):
            if key+'_ref' in row:
                del row[key+'_ref'];row[key]=artifact['results'][i][key]
    cases.append(measurement('gate-logs-by-reference',encode(full),encode(summary,True),restored==full))
    result={'suite':'token-efficiency-v1','metric':'UTF-8 bytes; actual tokens and native LLM quality unmeasured',
            'passed':all(c['data_equivalent'] and c['after_utf8_bytes']<c['before_utf8_bytes'] for c in cases),
            'cases':cases,'gates':full,
            'sources_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('omega/context.py','omega/__main__.py','tests/test_context.py','benchmarks/token_efficiency.py')},
            'claude_native_evaluated':False}
    if '--write-report' in sys.argv:
        dest=ROOT/'docs/evidence/token-efficiency.json'
        dest.write_text(encode(result)+'\n')
    print(encode({k:v for k,v in result.items() if k!='gates'}))
    return 0 if result['passed'] else 1


if __name__=='__main__':sys.exit(main())
