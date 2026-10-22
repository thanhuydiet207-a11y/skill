"""Explain OMEGA decisions, never claim to override platform or organization policy."""
from pathlib import Path
import re
import shlex
from omega.arguments import parser,validate
from omega.safety import source_path,artifact_path

ENGINE=Path(__file__).resolve().parent.parent
PROTECTED={'.git','.claude','omega','tests','benchmarks','.github','.omega'}
SAFE_COMMANDS={'doctor','map','plan','audit','benchmark','gates','memory','memory-read','context',
               'rollback-check','candidate','compare','change-plan','change-check','change-attempt','isolate',
               'skill-compatibility-audit','effective-policy-explainer','workflow-handoff-contract',
               'skill-interference-benchmark','project-workflow-adapter','evidence-reconciler',
               'memory-reconciliation','context-sufficiency-check'}


def explain(payload,root=ENGINE):
    root=Path(root).resolve()
    report={'allowed':False,'reason':'Invalid event','rule_source':'omega/policy.py',
            'scope':'OMEGA policy only','platform_decision':'unknown','command':None}
    def answer(allowed,reason):return {**report,'allowed':allowed,'reason':reason}
    if not isinstance(payload,dict) or payload.get('hook_event_name')!='PreToolUse':return answer(False,'Unexpected event')
    cwd=payload.get('cwd')
    if not isinstance(cwd,str) or not Path(cwd).is_absolute() or Path(cwd).resolve()!=root:return answer(False,'Unexpected working directory')
    tool=payload.get('tool_name');data=payload.get('tool_input')
    if not isinstance(data,dict):return answer(False,'Invalid tool input')
    if tool in ('Edit','Write'):
        try:
            if not isinstance(data.get('file_path'),str):raise ValueError('Missing path')
            path=source_path(root,data['file_path']);rel=path.relative_to(root)
        except (ValueError,OSError):return answer(False,'Private, symlink or escaping path')
        if rel.parts[0] in PROTECTED or rel.name in ('CLAUDE.md','.gitignore','omega_cli.py'):
            return answer(False,'Policy/config changes need separate review')
        return answer(True,'Scoped repository edit; task scope still applies')
    if tool!='Bash':return answer(False,'Unknown tool requires review')
    command=data.get('command')
    if not isinstance(command,str) or not command or len(command)>8192:return answer(False,'Invalid command')
    # Shell substitutions and composition are forbidden even inside quoted arguments.
    if any(c in command for c in '\n\r\0;$`|&<>*?[]{}!'):
        return answer(False,'Shell composition or expansion refused')
    if data.get('run_in_background',False):return answer(False,'Background command requires review')
    try:argv=shlex.split(command,posix=True)
    except ValueError:return answer(False,'Malformed shell quoting')
    if argv in (['git','status','--short'],['git','diff','--check'],['git','diff','--stat']):
        return answer(True,'Allowlisted read-only Git command')
    if not argv or argv[0] not in ('python3','python'):return answer(False,'Executable outside allowlist')
    if argv[1:3]==['-m','omega']:
        if root!=ENGINE:return answer(False,'Use the absolute OMEGA runner for another project')
        words=argv[3:]
    elif len(argv)>1 and Path(argv[1]).is_absolute() and Path(argv[1]).resolve()==ENGINE/'omega_cli.py':
        words=argv[2:]
    else:return answer(False,'Unrecognized runner')
    try:
        args=parser(policy=True).parse_args(words);validate(args)
        if args.command not in SAFE_COMMANDS:raise ValueError('Unreviewed command')
        report['command']=args.command
        if args.project_root and Path(args.project_root).resolve()!=root:raise ValueError('Project root mismatch')
        if not args.project_root and root!=ENGINE:raise ValueError('Explicit project root required')
        if args.gate_config:artifact_path(root,args.gate_config,'configs')
        if args.command=='isolate' and (not args.name or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,60}',args.name)):
            raise ValueError('Invalid branch name')
        if args.worktree:artifact_path(root,args.worktree,'worktrees',False)
        for value in args.allow:source_path(root,value)
        for value,kind in ((args.record,'memory' if args.command in ('memory-read','memory-reconciliation') else 'changes'),
                           (args.baseline,'baselines'),(args.candidate,'candidates')):
            if value:artifact_path(root,value,kind)
        for value in args.evidence:artifact_path(root,value,'evidence')
        for value in args.select:
            match=re.fullmatch(r'(.+):[1-9][0-9]*:[1-9][0-9]*',value)
            source_path(root,match[1] if match else value)
        if not 1<=args.max_bytes<=24000:raise ValueError('Invalid byte budget')
        # Scans outside project and user input documents require explicit review.
        for value in args.skill_root+args.hook_config:
            path=Path(value) if Path(value).is_absolute() else root/value
            if not path.resolve().is_relative_to(root):raise ValueError('External scan root requires review')
        if args.input:
            path=(root/args.input).resolve()
            if not path.is_relative_to(root):raise ValueError('Input escapes project')
    except (ValueError,OSError,TypeError):return answer(False,'Arguments outside reviewed OMEGA scope')
    return answer(True,'Validated OMEGA argv; trusted code/config and platform permissions still required')
