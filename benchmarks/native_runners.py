"""Actual dependency-free Node/JUnit workflow; no npm, network, model or deployment."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ROOT=Path(__file__).resolve().parent.parent


def main(report_file=False):
    node=shutil.which('node')
    if not node:raise ValueError('Node is required; no runtime will be installed automatically')
    base=ROOT/'.omega/native-runners'
    if any(p.is_symlink() for p in (base,*base.parents)):raise ValueError('Symlink fixture path refused')
    fixture=base/uuid.uuid4().hex;fixture.mkdir(parents=True)
    (fixture/'.gitignore').write_text('.omega/\n')
    source=fixture/'calc.cjs';source.write_text('exports.add = (a, b) => a - b;\n')
    (fixture/'sum.test.cjs').write_text("const test = require('node:test'); const assert = require('node:assert/strict');\nconst { add } = require('./calc.cjs');\ntest('addition', () => assert.equal(add(2, 3), 5));\ntest.skip('deliberately deferred', () => {});\n")
    def run(argv,expected=0):
        proc=subprocess.run(argv,cwd=fixture,text=True,capture_output=True,timeout=40)
        if proc.returncode!=expected:raise ValueError(f'Native fixture command failed: {argv[0]}, exit {proc.returncode}')
        return proc
    run(['git','init','-q','-b','omega/native-junit']);run(['git','add','.'])
    run(['git','-c','user.name=OMEGA fixture','-c','user.email=omega@example.invalid','commit','-qm','broken Node fixture'])
    cli=[sys.executable,str(ROOT/'omega_cli.py'),'--project-root',str(fixture)]
    tests=[node,'--test','--test-reporter=junit','sum.test.cjs']
    config={'schema':1,'test_adapter':'junit','gates':{
        'build':[node,'--check','calc.cjs'],'tests':tests,
        'security':[*cli,'audit','--select','calc.cjs','--select','sum.test.cjs','--compact'],
        'regression':tests}}
    if report_file:
        config['test_report']='.omega/reports/{run_id}/junit.xml'
        config['gates']['tests']=[node,'--test','--test-reporter=spec','--test-reporter-destination=stdout',
                                  '--test-reporter=junit','--test-reporter-destination={report_path}','sum.test.cjs']
    directory=fixture/'.omega/configs';directory.mkdir(parents=True)
    (directory/'gates.json').write_text(json.dumps(config))
    command=[*cli,'gates','--gate-config','.omega/configs/gates.json','--summary','--compact']
    before=json.loads(run(command,1).stdout)
    source.write_text('exports.add = (a, b) => a + b;\n')
    after=json.loads(run(command).stdout)
    if before['passed'] or not after['passed'] or after['test_outcomes']['passed']!=1 or after['test_outcomes']['skipped']!=1:raise ValueError('Unexpected native outcome counts')
    if report_file and next(x for x in before['results'] if x['gate']=='tests')['report']['path']==next(x for x in after['results'] if x['gate']=='tests')['report']['path']:raise ValueError('Report namespace was reused')
    report={'fixture':str(fixture.relative_to(ROOT)),'node_version':run([node,'--version']).stdout.strip(),
            'adapter':'junit','before_passed':before['passed'],'after_passed':after['passed'],
            'test_outcomes':after['test_outcomes'],'source_sha256':__import__('hashlib').sha256(source.read_bytes()).hexdigest(),
            'gate_exit_codes':{r['gate']:r['exit_code'] for r in after['results']},'evidence':str((fixture/after['evidence']).relative_to(ROOT)),
            'limits':'Node built-in test runner only; Jest and Go native unverified; regression repeats fixture tests; JS security uses text rules only',
            'network_used':False,'dependencies_installed':False,'native_claude_executed':False}
    report['structured_report_file']=report_file
    if report_file:report['report_metadata']=next(x for x in after['results'] if x['gate']=='tests')['report']
    print(json.dumps(report,ensure_ascii=False,indent=2));return 0


if __name__=='__main__':
    try:
        if sys.argv[1:] not in ([],['--report-file']):raise ValueError('Supported option: --report-file')
        sys.exit(main('--report-file' in sys.argv[1:]))
    except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
        print(json.dumps({'error':str(exc)}),file=sys.stderr);sys.exit(2)
