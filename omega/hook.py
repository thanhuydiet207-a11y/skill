"""Opt-in conservative PreToolUse adapter. NOT activated in Claude settings.

Denied requests exit 2; allowed requests exit 0. Verify this contract against
installed Claude Code before enabling. This is defense in depth, not a sandbox.
"""
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
from omega.policy import explain


def authorize(payload):
    result=explain(payload,ROOT)
    return result['allowed'],result['reason']


def main():
    try:
        raw=sys.stdin.read(65537)
        if len(raw.encode('utf-8'))>65536:raise ValueError('Oversized event')
        allowed,reason=authorize(json.loads(raw))
    except (ValueError,OSError,TypeError):allowed,reason=False,'Malformed hook event'
    if not allowed:print('OMEGA blocked: '+reason,file=sys.stderr)
    return 0 if allowed else 2


if __name__=='__main__':sys.exit(main())
