"""unittest entrypoint that rejects empty/all-skipped suites and reports outcomes."""
import argparse
import json
from pathlib import Path
import sys
import unittest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--start',default='tests');p.add_argument('--pattern',default='test_*.py')
    args=p.parse_args()
    sys.path.insert(0,str(Path.cwd()))  # Target tests intentionally import their own application.
    suite=unittest.defaultTestLoader.discover(args.start,pattern=args.pattern)
    result=unittest.TextTestRunner(verbosity=2,stream=sys.stdout).run(suite)
    outcomes={'run':result.testsRun};seen=set()
    # unittest records one entry per failed subtest but testsRun counts methods; count each method once, worst outcome first.
    for key,tests in (('errors',[t for t,_ in result.errors]),('failed',[t for t,_ in result.failures]),
                      ('unexpected_successes',result.unexpectedSuccesses),('expected_failures',[t for t,_ in result.expectedFailures]),
                      ('skipped',[t for t,_ in result.skipped])):
        methods={getattr(t,'test_case',t) for t in tests}-seen
        outcomes[key]=len(methods);seen|=methods
    outcomes['passed']=outcomes['run']-sum(outcomes[x] for x in ('failed','errors','skipped','expected_failures','unexpected_successes'))
    print('OMEGA_TEST_RESULT '+json.dumps(outcomes,sort_keys=True))
    if not result.wasSuccessful():return 1
    return 0 if outcomes['passed']>0 else 5


if __name__=='__main__':sys.exit(main())
