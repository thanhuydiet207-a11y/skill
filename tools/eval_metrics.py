"""Per-run usage, tool and outcome metrics from `claude plugin eval` results.

Reads each results directory's aggregate-result.json and, when a run kept its
trace (`--keep-temp`), the trace's final `result` event for provider-reported
tokens. A run without a trace keeps tokens null: byte or line counts are never
reported as tokens.

Usage: python3 tools/eval_metrics.py LABEL=RESULTS_DIR [...] [--json OUT]
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess

MODEL_KEYS={'inputTokens':'input','cacheReadInputTokens':'cache_read','cacheCreationInputTokens':'cache_write','outputTokens':'output'}
TOKEN_KEYS={'input_tokens':'input','cache_read_input_tokens':'cache_read','cache_creation_input_tokens':'cache_write','output_tokens':'output'}


def trace_metrics(path):
    trace=Path(path) if path else None
    if trace is None or not trace.is_file():return None
    result=None;tools=Counter();skills=Counter();agents=Counter()
    with trace.open(encoding='utf-8',errors='replace') as stream:
        for line in stream:
            try:event=json.loads(line)
            except ValueError:continue
            if not isinstance(event,dict):continue
            if event.get('type')=='assistant':
                for block in (event.get('message') or {}).get('content') or []:
                    if isinstance(block,dict) and block.get('type')=='tool_use':
                        tools[str(block.get('name'))]+=1
                        if block.get('name')=='Skill':skills[str((block.get('input') or {}).get('skill'))]+=1
                        if block.get('name')=='Agent':agents[str((block.get('input') or {}).get('subagent_type'))]+=1
            elif event.get('type')=='result':result=event  # The last result event covers the whole session.
    if result is None:return None
    usage=result.get('usage') or {}
    per_model={name:{short:(row.get(key) or 0) for key,short in MODEL_KEYS.items()} for name,row in (result.get('modelUsage') or {}).items()}
    # modelUsage covers every model that served the run, subagents included; `usage` alone may cover only the main thread.
    tokens={short:sum(m[short] for m in per_model.values()) for short in MODEL_KEYS.values()} if per_model else {name:usage.get(key) for key,name in TOKEN_KEYS.items()}
    return {'tokens':tokens,'models':sorted(per_model),'tokens_by_model':per_model,
            'tool_calls':dict(tools),'skills':dict(skills),'agents':dict(agents),'subagents':(result.get('subagent_stats') or {}).get('spawned',0)}


def load(label,directory):
    data=json.loads((Path(directory)/'aggregate-result.json').read_text(encoding='utf-8'))
    rows=[]
    for case in data['cases']:
        if '.omega/' in case['dir']:continue  # Stale copies under packaging exports are not suite cases.
        for arm,runs in case['arms'].items():
            for index,run in enumerate(runs):
                rows.append({'label':label,'case':case['name'],'arm':arm,'run':index,'score':run['score'],'passed':run['passed'],
                             'error':run.get('error'),'cost_usd':run['costUsd'],'duration_s':run['durationSeconds'],'turns':run['turns'],
                             'indicators':{g['name']:g['passed'] for g in run['graders'] if g.get('withOnly')},
                             **(trace_metrics(run.get('tracePath')) or {'tokens':None})})
    return {'label':label,'directory':str(directory),'claude_version':data.get('claudeVersion'),'started_at':data.get('startedAt')},rows


def mean(values):
    values=[v for v in values if v is not None]
    return round(sum(values)/len(values),4) if values else None


def summarize(rows):
    groups={}
    for row in rows:groups.setdefault((row['case'],row['label'],row['arm']),[]).append(row)
    summary=[]
    for (case,label,arm),runs in sorted(groups.items()):
        # A run that errored (API/session limit, scaffold) was never graded: report it apart, not as a failure or zero tokens.
        items=[r for r in runs if not r['error']]
        traced=[r for r in items if r['tokens']]
        successes=sum(r['passed'] for r in items)
        if not items:
            summary.append({'case':case,'label':label,'arm':arm,'runs':len(runs),'errored_runs':len(runs),'success_rate':None,'mean_score':None,
                            'mean_cost_usd':None,'cost_per_success_usd':None,'mean_duration_s':None,'mean_turns':None,'runs_with_tokens':0,
                            'mean_input_tokens':None,'mean_output_tokens':None,'mean_tool_calls':None,'skill_invocation_rate':None})
            continue
        summary.append({'case':case,'label':label,'arm':arm,'runs':len(runs),'errored_runs':len(runs)-len(items),'success_rate':round(successes/len(items),4),
                        'mean_score':mean(r['score'] for r in items),'mean_cost_usd':mean(r['cost_usd'] for r in items),
                        # Total spend divided by successful runs; undefined when nothing succeeded.
                        'cost_per_success_usd':round(sum(r['cost_usd'] for r in items)/successes,4) if successes else None,
                        'mean_duration_s':mean(r['duration_s'] for r in items),'mean_turns':mean(r['turns'] for r in items),
                        'runs_with_tokens':len(traced),
                        'mean_input_tokens':mean(sum(r['tokens'][k] or 0 for k in ('input','cache_read','cache_write')) for r in traced) if traced else None,
                        'mean_output_tokens':mean(r['tokens']['output'] for r in traced) if traced else None,
                        'mean_tool_calls':mean(sum(r['tool_calls'].values()) for r in traced) if traced else None,
                        'skill_invocation_rate':round(sum(bool(r['skills']) for r in traced)/len(traced),4) if traced else None,
                        # How often each agent type was delegated to, as a share of traced runs; 'none' means no delegation.
                        'delegation':{k:round(v/len(traced),4) for k,v in sorted(Counter((a for r in traced for a in (r['agents'] or {'none':1}))).items())} if traced else None,
                        'models':sorted({m for r in traced for m in r['models']}) if traced else None})
    return summary


def table(summary):
    def cell(value):return '—' if value is None else str(value)
    head=['case','label','arm','runs','errored_runs','success_rate','cost_per_success_usd','mean_input_tokens','mean_output_tokens','mean_tool_calls','skill_invocation_rate','delegation','models','mean_duration_s']
    lines=['| '+' | '.join(head)+' |','|'+'---|'*len(head)]
    lines+=['| '+' | '.join(cell(row[k]) for k in head)+' |' for row in summary]
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('results',nargs='+',help='LABEL=DIRECTORY holding aggregate-result.json')
    parser.add_argument('--json',help='write meta, per-run rows and summary to this file')
    args=parser.parse_args()
    sources=[];rows=[]
    for item in args.results:
        label,sep,directory=item.partition('=')
        if not sep or not label or not directory:parser.error(f'expected LABEL=DIRECTORY, got {item!r}')
        meta,items=load(label,directory);sources.append(meta);rows+=items
    head=subprocess.run(['git','rev-parse','HEAD'],cwd=Path(__file__).resolve().parent,capture_output=True,text=True).stdout.strip() or None
    summary=summarize(rows)
    if args.json:Path(args.json).write_text(json.dumps({'engine_head':head,'sources':sources,'runs':rows,'summary':summary},indent=1,ensure_ascii=False)+'\n',encoding='utf-8')
    print(table(summary))


if __name__=='__main__':main()
