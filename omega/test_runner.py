"""unittest entrypoint that rejects empty/all-skipped suites and reports outcomes."""
import argparse
import json
import sys
import unittest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--start',default='tests');p.add_argument('--pattern',default='test_*.py')
    args=p.parse_args()
    suite=unittest.defaultTestLoader.discover(args.start,pattern=args.pattern)
    result=unittest.TextTestRunner(verbosity=2,stream=sys.stdout).run(suite)
    outcomes={'run':result.testsRun,'failed':len(result.failures),'errors':len(result.errors),
              'skipped':len(result.skipped),'expected_failures':len(result.expectedFailures),
              'unexpected_successes':len(result.unexpectedSuccesses)}
    outcomes['passed']=outcomes['run']-sum(outcomes[x] for x in ('failed','errors','skipped','expected_failures','unexpected_successes'))
    print('OMEGA_TEST_RESULT '+json.dumps(outcomes,sort_keys=True))
    if not result.wasSuccessful():return 1
    return 0 if outcomes['passed']>0 else 5


if __name__=='__main__':sys.exit(main())
