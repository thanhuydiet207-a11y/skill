#!/usr/bin/env python3
"""Absolute-path entrypoint: trusted engine location, explicit target repository."""
import json
import sys
sys.dont_write_bytecode = True  # Installed plugin code is read-only; state belongs to the target repository.
from omega.__main__ import main

if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(json.dumps({'error':str(exc)}),file=sys.stderr);sys.exit(2)
