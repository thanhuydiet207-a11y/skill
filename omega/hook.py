"""Opt-in conservative PreToolUse adapter. NOT activated in Claude settings.

Denied requests exit 2; allowed requests exit 0. Verify this contract against
installed Claude Code before enabling. This is defense in depth, not a sandbox.
"""
import json
from pathlib import Path
import sys
from omega.__main__ import ROOT
from omega.safety import source_path

READ_COMMANDS = {'git status --short', 'git diff --check', 'git diff --stat',
                 'python3 -m omega doctor', 'python3 -m omega map',
                 'python3 -m omega benchmark', 'python3 -m omega audit',
                 'python3 -m omega gates', 'python3 -m omega rollback-check'}


def authorize(payload):
    if not isinstance(payload,dict): return False, 'Invalid event'
    if payload.get('hook_event_name') != 'PreToolUse': return False, 'Unexpected event'
    cwd=payload.get('cwd')
    if not isinstance(cwd,str) or not Path(cwd).is_absolute() or Path(cwd).resolve()!=ROOT:
        return False,'Unexpected working directory'
    tool = payload.get('tool_name')
    data = payload.get('tool_input')
    if not isinstance(data,dict):return False,'Invalid tool input'
    if tool in ('Write','Edit'):
        value=data.get('file_path')
        if not isinstance(value,str):return False,'Missing file path'
        try:
            p=source_path(ROOT,value)
        except (ValueError,OSError):return False,'Path escapes repository'
        relative=p.relative_to(ROOT)
        if relative.parts[0] in ('.git','.claude','omega','tests','benchmarks','.github','.omega') or relative.name in ('CLAUDE.md', '.gitignore', '.env') or relative.name.startswith('.env.'):
            return False,'Policy/config changes need separate human review'
        return True,'Scoped repository edit'
    if tool == 'Bash':
        command=data.get('command')
        if not isinstance(command,str) or command not in READ_COMMANDS:
            return False,'Command outside conservative allowlist; request human review'
        if data.get('run_in_background',False):return False,'Background command requires review'
        return True,'Allowlisted command; executable/config must already be trusted'
    return False,'Unknown tool requires review'


def main():
    try:
        raw=sys.stdin.read(65537)
        if len(raw.encode('utf-8'))>65536:raise ValueError('Oversized event')
        allowed,reason=authorize(json.loads(raw))
    except (ValueError,OSError,TypeError):allowed,reason=False,'Malformed hook event'
    if not allowed:print('OMEGA blocked: '+reason,file=sys.stderr)
    return 0 if allowed else 2


if __name__=='__main__':sys.exit(main())
