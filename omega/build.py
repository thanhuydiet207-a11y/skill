"""Engine build gate: Python compilation and pinned TypeScript compiler, no installation."""
from pathlib import Path
import sys
from omega.process import execute

ROOT=Path(__file__).resolve().parent.parent


def main():
    commands=[['python3','-m','compileall','-q','omega','tests','benchmarks','omega_cli.py'],
              ['node',str(ROOT/'integration/typescript/node_modules/typescript/bin/tsc'),'--noEmit','-p',str(ROOT/'integration/typescript/tsconfig.json')]]
    for command in commands:
        result=execute(command,ROOT,timeout=45)
        if result['output']:print(result['output'],end='')
        if result['exit_code']:
            if command[0]=='node':print('TypeScript build failed; install reviewed pinned dev tools with npm ci --prefix integration/typescript --ignore-scripts before engine gates.',file=sys.stderr)
            return result['exit_code']
    return 0


if __name__=='__main__':sys.exit(main())
