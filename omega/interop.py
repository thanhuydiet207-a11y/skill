"""Static interoperability inspection and explicit workflow contracts; no skill execution."""
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
from omega.frontmatter import parse
from omega.safety import source_path


def bounded_text(path,limit=8192):
    path=Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>limit:raise ValueError('Missing, symlink or oversized inspection source')
    return path.read_text(encoding='utf-8')


def compatibility(root,skill_roots=(),hook_configs=(),contracts=None):
    root=Path(root).resolve();roots=list(skill_roots) or [str(root/'.claude/skills')]
    if len(roots)>8 or len(hook_configs)>16:raise ValueError('Inspection root budget exceeded')
    skills=[];findings=[];complete=True;seen=set();hook_events=defaultdict(int)
    for value in roots:
        location=Path(value) if Path(value).is_absolute() else root/value
        if location.is_symlink() or not location.is_dir():
            findings.append({'kind':'unreadable-root','source':str(location)});complete=False;continue
        location=location.resolve();directories=0
        for directory,dirs,files in os.walk(location,followlinks=False):
            directories+=1
            if directories>512 or len(skills)>=128:
                complete=False;findings.append({'kind':'inspection-budget','source':str(location)});break
            for name in list(dirs):
                if (Path(directory)/name).is_symlink():
                    dirs.remove(name);complete=False;findings.append({'kind':'symlink-not-scanned','source':str(Path(directory)/name)})
            if 'SKILL.md' not in files:continue
            path=Path(directory)/'SKILL.md'
            if str(path) in seen:continue
            seen.add(str(path))
            try:text=bounded_text(path);doc=parse(text)
            except (OSError,ValueError):
                complete=False;findings.append({'kind':'unreadable-skill','source':str(path)});continue
            name=doc['fields'].get('name')
            if not isinstance(name,str) or not re.fullmatch('[a-z0-9][a-z0-9-]{0,63}',name):
                complete=False;findings.append({'kind':'unresolved-skill-identity','source':str(path)});continue
            if not doc['supported'] or doc['unknown_fields']:
                complete=False;findings.append({'kind':'frontmatter-needs-review','skill':name})
            manual=doc['fields'].get('disable-model-invocation') is True
            signals=[key for key,pattern in (('workflow-language',r'orchestrat|before any|before every|MANDATORY'),
                     ('git-language',r'git worktree|git switch|git checkout'),('learning-language',r'global memory|instinct|auto.memory')) if re.search(pattern,text,re.I)]
            skills.append({'name':name,'path':str(path),'sha256':hashlib.sha256(text.encode()).hexdigest(),
                           'activation':'explicit' if manual else 'model-eligible-or-unspecified','signals':signals,
                           'side_effects':'unverified; document signals are not execution evidence'})
    by_name=defaultdict(list)
    for skill in skills:by_name[skill['name']].append(skill['path'])
    for name,paths in by_name.items():
        if len(paths)>1:findings.append({'kind':'same-name-across-roots','skill':name,'sources':paths})
    hooks=[]
    for value in hook_configs:
        path=Path(value) if Path(value).is_absolute() else root/value
        try:
            raw=bounded_text(path,1048576);doc=json.loads(raw)
            event_map=doc.get('hooks') if isinstance(doc,dict) else None
            if not isinstance(event_map,dict):raise ValueError('Invalid hooks object')
            for event,entries in event_map.items():
                if not isinstance(entries,list):raise ValueError('Invalid hook entries')
                for entry in entries:
                    if not isinstance(entry,dict) or not isinstance(entry.get('hooks'),list):raise ValueError('Invalid hook entry')
                    for hook in entry['hooks']:
                        if not isinstance(hook,dict):raise ValueError('Invalid hook')
                        hook_events[event]+=1
                        hooks.append({'event':event,'matcher':entry.get('matcher'),'type':hook.get('type'),
                                      'source':str(path),'command_sha256':hashlib.sha256(str(hook.get('command','')).encode()).hexdigest()})
        except (ValueError,OSError):complete=False;findings.append({'kind':'hook-config-needs-review','source':str(path)})
    for event,count in hook_events.items():
        if count>1:findings.append({'kind':'overlapping-hook-event-review','event':event,'count':count})
    if contracts is not None:
        if not isinstance(contracts,dict) or not isinstance(contracts.get('nodes'),list):raise ValueError('Expected a workflow contract object')
        contract=handoff(root,contracts)
        findings.extend({'kind':'workflow-conflict','detail':x} for x in contract['issues'])
    return {'passed':complete and not findings,'complete_for_selected_roots':complete,'skills':skills,'hooks':hooks,
            'findings':findings,'runtime_resolver_precedence':'unverified','global_scopes_scanned':False,
            'scope':'selected explicit files only; static signals do not certify native compatibility'}


def handoff(root,document):
    if not isinstance(document,dict) or not isinstance(document.get('nodes'),list) or not 1<=len(document['nodes'])<=24:raise ValueError('Expected 1..24 workflow nodes')
    budget=document.get('max_agents',2)
    if type(budget) is not int or not 1<=budget<=2:raise ValueError('Workflow agent budget must be 1 or 2')
    nodes={};issues=[]
    for node in document['nodes']:
        if not isinstance(node,dict) or not isinstance(node.get('id'),str) or not re.fullmatch('[a-z][a-z0-9-]{0,63}',node['id']) or node['id'] in nodes:raise ValueError('Invalid/duplicate node id')
        if node.get('role') not in ('orchestrator','worker','reviewer','memory'):raise ValueError('Unknown workflow role')
        if type(node.get('agents',1)) is not int or not 0<=node.get('agents',1)<=budget:raise ValueError('Node exceeds agent budget')
        for key in ('after','writes','owns'):
            if not isinstance(node.get(key,[]),list) or any(not isinstance(x,str) for x in node.get(key,[])):raise ValueError('Invalid workflow list')
        copy=dict(node);copy['writes']=[str(source_path(root,x).relative_to(root)) for x in node.get('writes',[])]
        nodes[node['id']]=copy
    if sum(n['role']=='orchestrator' for n in nodes.values())!=1:issues.append('Exactly one orchestrator is required')
    owners=defaultdict(list)
    for name,node in nodes.items():
        for resource in node.get('owns',[]):
            if resource not in ('workflow','git','gates','memory'):raise ValueError('Unknown ownership resource')
            owners[resource].append(name)
        if any(x not in nodes or x==name for x in node.get('after',[])):raise ValueError('Unknown/self dependency')
    for resource,names in owners.items():
        if len(names)>1:issues.append('Multiple owners of '+resource+': '+', '.join(names))
    ancestors={name:set() for name in nodes};remaining=set(nodes);done=set();batches=[]
    while remaining:
        ready=sorted(name for name in remaining if set(nodes[name].get('after',[]))<=done)
        if not ready:issues.append('Workflow dependency cycle');break
        batch=[];used=0
        for name in ready:
            cost=nodes[name].get('agents',1)
            if used+cost<=budget:batch.append(name);used+=cost
        if not batch:issues.append('No schedule fits the budget');break
        for name in batch:
            for parent in nodes[name].get('after',[]):ancestors[name].update(ancestors[parent]|{parent})
        batches.append(batch);done.update(batch);remaining.difference_update(batch)
    ids=sorted(nodes)
    if not remaining:
        for i,left in enumerate(ids):
            for right in ids[i+1:]:
                shared=set(nodes[left]['writes'])&set(nodes[right]['writes'])
                if shared and left not in ancestors[right] and right not in ancestors[left]:
                    issues.append('Unordered writers '+left+' / '+right+': '+', '.join(sorted(shared)))
    return {'passed':not issues,'issues':issues,'schedule':batches,'max_agents':budget,
            'execution':'validated plan only; this command does not dispatch agents or mutate Git'}


def project_adapter(root):
    root=Path(root).resolve();options=[];missing=[]
    if (root/'package.json').is_file():
        data=json.loads(bounded_text(source_path(root,'package.json'),1048576))
        scripts=data.get('scripts',{})
        if not isinstance(scripts,dict):raise ValueError('Invalid package scripts')
        options.append({'stack':'node','build':['npm','run','build'] if 'build' in scripts else None,
                        'tests':['npm','test','--','--json'] if 'test' in scripts else None,
                        'test_adapter':'jest','assumption':'Only use Jest adapter if test script actually emits Jest JSON; other runners need another adapter'})
    if (root/'go.mod').is_file():options.append({'stack':'go','build':['go','build','./...'],'tests':['go','test','-json','./...'],'test_adapter':'go'})
    if any((root/x).is_file() for x in ('pyproject.toml','requirements.txt')) or (root/'tests').is_dir():
        options.append({'stack':'python','build':['python3','-m','compileall','-q','.'],
                        'tests':'Use reviewed unittest runner or provide JUnit XML from the project runner','test_adapter':'omega-or-junit'})
    if not options:missing.append('No supported workflow detected from explicit manifests/tests directory')
    missing+=['Review and supply security and regression commands; they are not inferred as passing',
              'Review build/test command and runner output format before saving .omega/configs/gates.json']
    return {'passed':False,'status':'proposal-needs-review','proposals':options,'requirements':missing,
            'dependencies_installed':False,'files_written':False,'commands_executed':False}
