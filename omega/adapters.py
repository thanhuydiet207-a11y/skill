"""Strict test outcome adapters. Exit zero alone never proves tests ran."""
import json
import xml.etree.ElementTree as ET

KEYS=('run','passed','failed','errors','skipped','expected_failures','unexpected_successes')


def normalized(counts):
    if not isinstance(counts,dict) or any(type(counts.get(k)) is not int or counts[k]<0 for k in KEYS):return None
    if counts['run']!=sum(counts[k] for k in KEYS if k!='run') or counts['passed']<=0:return None
    if any(counts[k] for k in ('failed','errors','unexpected_successes')):return None
    return {k:counts[k] for k in KEYS}


def outcomes(result,adapter='omega'):
    if type(result.get('exit_code')) is not int or result['exit_code']!=0:return None
    text=result.get('output','')
    if not isinstance(text,str) or len(text.encode())>1048576:return None
    try:
        counts=dict.fromkeys(KEYS,0)
        if adapter=='omega':
            text=result.get('output_tail') or text
            lines=[line[18:] for line in text.splitlines() if line.startswith('OMEGA_TEST_RESULT ')]
            return normalized(json.loads(lines[0])) if len(lines)==1 else None
        if result.get('truncated'):return None
        if adapter=='jest':
            data=json.loads(text)
            fields=('numTotalTests','numPassedTests','numFailedTests','numPendingTests','numTodoTests')
            if not isinstance(data,dict) or any(type(data.get(k)) is not int or data[k]<0 for k in fields):return None
            counts.update(run=data['numTotalTests'],passed=data['numPassedTests'],failed=data['numFailedTests'],skipped=data['numPendingTests']+data['numTodoTests'])
            if data.get('success') is not True:return None
        elif adapter=='go':
            terminal={};started=set()
            for line in text.splitlines():
                event=json.loads(line)
                if not isinstance(event,dict):return None
                package=event.get('Package');test=event.get('Test');action=event.get('Action')
                if action=='fail' and not test:return None
                if test:
                    if not isinstance(test,str) or not isinstance(package,str):return None
                    key=(package,test)
                    if action=='run':
                        if key in started:return None
                        started.add(key)
                    if action in ('pass','fail','skip'):
                        if key in terminal:return None
                        terminal[key]=action
            if not terminal or any(k not in terminal for k in started):return None
            counts.update(run=len(terminal),passed=sum(x=='pass' for x in terminal.values()),failed=sum(x=='fail' for x in terminal.values()),skipped=sum(x=='skip' for x in terminal.values()))
        elif adapter=='junit':
            if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():return None
            tree=ET.fromstring(text)
            if tree.tag not in ('testsuites','testsuite'):return None
            cases=list(tree.iter('testcase'))
            for case in cases:
                types=[tag for tag in ('failure','error','skipped') if case.find(tag) is not None]
                if len(types)>1:return None
                counts['run']+=1
                counts[{'failure':'failed','error':'errors','skipped':'skipped'}.get(types[0] if types else '', 'passed')]+=1
            for suite in tree.iter('testsuite'):
                actual=len(list(suite.iter('testcase')))
                if 'tests' in suite.attrib and int(suite.attrib['tests'])!=actual:return None
        else:return None
        return normalized(counts)
    except (ValueError,TypeError,KeyError,ET.ParseError):return None
