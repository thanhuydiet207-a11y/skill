#!/usr/bin/env bash
# Baseline copy plus one planted bug in a shared helper: normalized() accepts zero passed tests.
# It breaks one test in tests/test_hardening.py (named in the prompt) and one in tests/test_interop_core.py (not named).
set -euo pipefail
bash "$(dirname "$0")/../scaffold.sh"
sed -i "s/or counts\\['passed'\\]<=0:return None/or counts['passed']<0:return None/" omega/adapters.py
grep -q "counts\\['passed'\\]<0:return None" omega/adapters.py
git -c user.name=eval -c user.email=eval@localhost commit -q -am "baseline with planted bug"
