"""Bounded, read-only security rules. No execution, taint analysis or dependency scan."""
import ast
import hashlib
import os
from pathlib import Path
import re
from omega.io import bounded_json
from omega.safety import source_path


SECRET=re.compile(r'gh[pousr]_[A-Za-z0-9]{24,}|sk-(?:ant-)?[A-Za-z0-9_-]{24,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')
BYPASS=('--dangerously-skip-permissions','"bypassPermissions"','curl -k ','verify=False')


def python_findings(text):
    tree=ast.parse(text);aliases={};findings=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            for item in node.names:aliases[item.asname or item.name.split('.')[0]]=item.name if item.asname else item.name.split('.')[0]
        elif isinstance(node,ast.ImportFrom) and node.module:
            for item in node.names:aliases[item.asname or item.name]=node.module+'.'+item.name
    def name(node):
        if isinstance(node,ast.Name):return aliases.get(node.id,node.id)
        if isinstance(node,ast.Attribute):return name(node.value)+'.'+node.attr
        return ''
    for node in ast.walk(tree):
        if not isinstance(node,ast.Call):continue
        call=name(node.func);rule=None
        if call in ('eval','exec','builtins.eval','builtins.exec'):rule='python-dynamic-execution'
        elif call in ('os.system','os.popen'):rule='python-shell-execution'
        elif call in ('pickle.load','pickle.loads'):rule='python-pickle-deserialization'
        elif call=='ssl._create_unverified_context':rule='python-tls-verification-disabled'
        elif call.startswith('subprocess.') and call.rsplit('.',1)[-1] in ('run','Popen','call','check_call','check_output'):
            for kw in node.keywords:
                if kw.arg=='shell' and not (isinstance(kw.value,ast.Constant) and kw.value.value in (False,None)):
                    rule='python-subprocess-shell-or-dynamic';break
                if kw.arg is None:rule='python-subprocess-options-need-review'
        elif call.startswith('requests.'):
            if any(kw.arg=='verify' and isinstance(kw.value,ast.Constant) and kw.value.value is False for kw in node.keywords):rule='python-tls-verification-disabled'
        elif call=='yaml.load':
            safe=any(kw.arg=='Loader' and name(kw.value) in ('yaml.SafeLoader','yaml.CSafeLoader') for kw in node.keywords)
            if not safe:rule='python-unsafe-yaml-load'
        if rule:findings.append({'rule':rule,'line':node.lineno})
    return findings


def audit(root,selections=()):
    root=Path(root).resolve();chosen=list(selections) or (['.claude'] if (root/'.claude').exists() else [])
    if len(chosen)>32:raise ValueError('Security selection budget exceeded')
    findings=[];coverage=[];paths=set();exclusions=[];complete=True;directory_count=0
    def finding(path,rule,line=None):findings.append({'path':str(path),'rule':rule,'line':line})
    for value in chosen:
        try:
            entry=source_path(root,value)
            if not entry.exists():raise ValueError('Missing selection')
            if entry.is_file():paths.add(entry)
            elif entry.is_dir():
                for directory,dirs,files in os.walk(entry,followlinks=False):
                    directory_count+=1
                    if directory_count>256:raise ValueError('Directory budget exceeded')
                    for name in sorted(list(dirs)):
                        child=Path(directory)/name
                        if name=='__pycache__' and not child.is_symlink():
                            dirs.remove(name);exclusions.append({'path':str(child.relative_to(root)),'reason':'generated Python bytecode'});continue
                        try:source_path(root,str(child))
                        except ValueError:
                            dirs.remove(name);complete=False;finding(child.relative_to(root),'directory-not-scanned')
                    dirs.sort()
                    for name in sorted(files):paths.add(Path(directory)/name)
                    if len(paths)>256:raise ValueError('File budget exceeded')
            else:raise ValueError('Unsupported selection')
        except (OSError,ValueError):complete=False;finding(value,'selection-not-completely-scanned')
    used=0
    for path in sorted(paths):
        if len(coverage)>=256:complete=False;finding('selected-files','file-budget-exceeded');break
        relative=str(path.relative_to(root))
        try:
            safe=source_path(root,relative)
            if not safe.is_file() or safe.stat().st_size>1048576:raise ValueError('Missing or oversized source')
            used+=safe.stat().st_size
            if used>4194304:raise ValueError('Total input budget exceeded')
            raw=safe.read_bytes()
            if b'\0' in raw:raise ValueError('Binary input needs another scanner')
            text=raw.decode('utf-8');digest=hashlib.sha256(raw).hexdigest()
            coverage.append({'path':relative,'sha256':digest,'python_ast':path.suffix=='.py'})
            for match in SECRET.finditer(text):finding(relative,'possible-secret-literal',text.count('\n',0,match.start())+1)
            if '.claude' in path.relative_to(root).parts or path.suffix=='.json':
                for pattern in BYPASS:
                    if pattern in text:finding(relative,'permission-or-verification-bypass-pattern',text.count('\n',0,text.index(pattern))+1)
            if path.suffix=='.py':
                for row in python_findings(text):finding(relative,row['rule'],row['line'])
            if path.suffix=='.json':
                document=bounded_json(text)
                if isinstance(document,dict) and document.get('disableAllHooks') is True:finding(relative,'all-hooks-disabled')
                def permission_mode(value):
                    if isinstance(value,dict):
                        if any(key in ('defaultMode','permissionMode') and item=='bypassPermissions' for key,item in value.items()):return True
                        return any(permission_mode(item) for item in value.values())
                    if isinstance(value,list):return any(permission_mode(item) for item in value)
                    return False
                if permission_mode(document):finding(relative,'permission-mode-bypass')
        except (OSError,ValueError,SyntaxError,RecursionError):
            complete=False;finding(relative,'source-not-completely-scanned')
    return {'passed':complete and not findings,'complete_for_selected_paths':complete,'findings':findings,
            'coverage':coverage,'exclusions':exclusions,'files_scanned':len(coverage),'files_written':False,'commands_executed':False,
            'scope':'targeted Python AST, explicit bypass and possible-secret rules only; no taint/dependency/full-language assurance'}
