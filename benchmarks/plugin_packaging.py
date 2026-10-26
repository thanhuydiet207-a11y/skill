"""Export tracked plugin files and optionally test a local Claude install in isolated state.

No model request, dependency install, unredirected global configuration, deployment or cleanup.
Native probes use a local marketplace; incidental CLI network activity is not measured.
Native CLI path is an explicit trusted operator argument, never project input.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid
import zipfile

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from omega.process import execute
from omega.safety import source_path,artifact_path


def export_plugin(root,base):
    """Only tracked, bounded regular sources. Ignore/runtime trees are never shipped."""
    result=execute(['git','ls-files','-z'],root,capture_bytes=1048576)
    if result['exit_code'] or result['truncated']:raise ValueError('Cannot obtain complete tracked file list')
    # evals/ is a maintainer suite; exported copies under .omega/ would be rediscovered as duplicate eval cases.
    names=[x for x in result['output'].split('\0') if x and not x.startswith('evals/')]
    if not names or len(names)>512:raise ValueError('Plugin file count budget exceeded')
    manifest=[];total=0;payload=base/'marketplace'
    archive=base/'omega.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as bundle:
        for name in sorted(names):
            path=source_path(root,name)
            if not path.is_file() or path.stat().st_size>1048576:raise ValueError('Missing or oversized plugin source')
            with path.open('rb') as stream:data=stream.read(1048577)
            total+=len(data)
            if len(data)>1048576 or total>8388608:raise ValueError('Plugin byte budget exceeded')
            destination=artifact_path(root,str((payload/name).relative_to(root)),'plugin-packaging',False)
            destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            bundle.writestr(info,data)
            manifest.append({'path':name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
    for name in ('.claude-plugin/plugin.json','.claude-plugin/marketplace.json','.claude/skills/omega/SKILL.md','omega_cli.py'):
        if not (payload/name).is_file():raise ValueError('Stage all plugin files before export')
    return payload,archive,manifest


def native_probe(root,base,payload,cli):
    config=base/'claude-config';target=base/'target';target.mkdir()
    environment={**os.environ,'CLAUDE_CONFIG_DIR':str(config)};records=[]
    def run(argv,cwd=target,expected=0,config_dir=config):
        result=execute(argv,cwd,timeout=40,capture_bytes=131072,env={**environment,'CLAUDE_CONFIG_DIR':str(config_dir)})
        records.append(result)
        (base/'native-commands.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
        if result['exit_code']!=expected or any(result.get(x) for x in ('truncated','invalid_utf8','timed_out','output_limit_exceeded')):
            raise ValueError('Native plugin probe failed; inspect retained logs')
        return result
    version=run([cli,'--version'])['output'].strip()
    for manifest in ('plugin.json','marketplace.json'):
        result=run([cli,'plugin','validate','--strict','--json',str(payload/'.claude-plugin'/manifest)])
        validation=json.loads(result['output'])
        if validation.get('success') is not True or validation.get('manifest',{}).get('type')!=manifest.removesuffix('.json'):
            raise ValueError('Native manifest validation did not pass for the requested type')
    run([cli,'plugin','marketplace','add',str(payload),'--json'])
    run([cli,'plugin','install','omega@omega-marketplace','--scope','user','--json'])
    plugins=json.loads(run([cli,'plugin','list','--json'])['output'])
    installed=next(x for x in plugins if x['id']=='omega@omega-marketplace')
    cache=Path(installed['installPath']).resolve()
    if not cache.is_relative_to(config.resolve()) or not (cache/'omega_cli.py').is_file():raise ValueError('Plugin cache escaped isolated configuration')
    inventory=run([cli,'plugin','details','omega@omega-marketplace'])['output']
    zip_inventory=run([cli,'--plugin-dir',str(base/'omega.zip'),'plugin','details','omega'],config_dir=base/'zip-config')['output']
    for pattern in (r'Skills \(1\)\s+omega',r'Agents \(3\)',r'Hooks \(0\)',r'MCP servers \(0\)'):
        if not all(re.search(pattern,text) for text in (inventory,zip_inventory)):
            raise ValueError('Native inventory did not match one skill, three agents, no hooks/MCP')
    def cache_state():return {str(p.relative_to(cache)):hashlib.sha256(p.read_bytes()).hexdigest() for p in cache.rglob('*') if p.is_file()}
    before=cache_state()
    (target/'.gitignore').write_text('.omega/\n__pycache__/\n')
    (target/'omega.py').write_text('raise RuntimeError("Untrusted target omega must not be imported")\n')
    (target/'calc.py').write_text('def add(a,b):return a-b\n')
    (target/'checks').mkdir();(target/'checks/test_calc.py').write_text('import unittest\nfrom calc import add\nclass Calc(unittest.TestCase):\n    def test_sum(self):self.assertEqual(add(2,3),5)\n')
    run(['git','init','-q','-b','omega/plugin-fixture']);run(['git','add','.'])
    run(['git','-c','user.name=OMEGA fixture','-c','user.email=omega@example.invalid','commit','-qm','plugin target fixture'])
    engine=[sys.executable,'-B',str(cache/'omega_cli.py'),'--project-root',str(target)]
    mapped=json.loads(run([*engine,'map','--compact'])['output'])
    if 'calc.py' not in {x['path'] for x in mapped['files']}:raise ValueError('Installed engine did not inspect target')
    planned=json.loads(run([*engine,'plan','--compact'])['output'])
    if planned['skills']!=['omega'] or Path(planned.get('reference_root',''))!=cache:
        raise ValueError('Installed planner lost unified skill or trusted reference root')
    tests=[sys.executable,'-B',str(cache/'omega/test_runner.py'),'--start','checks']
    policy={'schema':1,'gates':{'build':[sys.executable,'-B','-m','compileall','-q','-f','--invalidation-mode','checked-hash','calc.py'],
        'tests':tests,'security':[*engine,'audit','--select','calc.py','--select','checks','--compact'],'regression':tests}}
    directory=target/'.omega/configs';directory.mkdir(parents=True);(directory/'gates.json').write_text(json.dumps(policy))
    gates=[*engine,'gates','--gate-config','.omega/configs/gates.json','--summary','--compact']
    red=json.loads(run(gates,expected=1)['output']);(target/'calc.py').write_text('def add(a,b):return a+b\n')
    green=json.loads(run(gates)['output'])
    if red['passed'] or not green['passed'] or green['test_outcomes']['passed']!=1:raise ValueError('Installed engine red-to-green workflow failed')
    if cache_state()!=before:raise ValueError('Installed engine wrote into plugin cache')
    return {'passed':True,'claude_version':version,'installed':installed,'inventory':inventory,'zip_inventory':zip_inventory,'records':records,
        'zip_inventory_verified':True,
        'target_map_verified':True,'target_shadow_module_not_imported':True,'cache_unchanged':True,
        'before_passed':red['passed'],'after_passed':green['passed'],'test_outcomes':green['test_outcomes'],
        'configuration_scope':str(config.relative_to(root)),'model_request_sent':False,
        'activation_trace_verified':False,'native_reasoning_quality_evaluated':False,'provider_tokens_measured':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--claude');args=parser.parse_args()
    check=execute(['git','check-ignore','--quiet','--','.omega/plugin-packaging/probe'],ROOT)
    if check['exit_code']:raise ValueError('Reviewed .omega ignore required')
    base=artifact_path(ROOT,'.omega/plugin-packaging/runs/'+uuid.uuid4().hex+'/placeholder','plugin-packaging',False).parent
    base.mkdir(parents=True,exist_ok=False)
    report={'passed':False,'source_head':execute(['git','rev-parse','HEAD'],ROOT)['output'].strip(),
        'source_snapshot':'Working file bytes from tracked paths; see file hashes, HEAD alone does not assert a clean checkout',
        'native':'not run; supply --claude ABS to run isolated install probe','model_request_sent':False}
    try:
        payload,archive,manifest=export_plugin(ROOT,base)
        report.update(archive=str(archive.relative_to(ROOT)),archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),files=manifest)
        if args.claude:
            cli=Path(args.claude)
            if not cli.is_absolute() or not cli.is_file():raise ValueError('Trusted absolute Claude CLI path required')
            report['native']={'state':'attempted','logs':str((base/'native-commands.json').relative_to(ROOT))}
            report['native']=native_probe(ROOT,base,payload,str(cli))
        report['passed']=True
    except (OSError,ValueError,StopIteration) as exc:report['error']=str(exc)
    (base/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'report':str((base/'result.json').relative_to(ROOT)),**report},ensure_ascii=False))
    return 0 if report['passed'] else 1


if __name__=='__main__':sys.exit(main())
