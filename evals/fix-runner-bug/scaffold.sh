#!/usr/bin/env bash
# Baseline copy plus one planted bug: an empty or all-skipped suite exits 0 instead of 5.
set -euo pipefail
bash "$(dirname "$0")/../scaffold.sh"
sed -i "s/outcomes\['passed'\]>0 else 5/outcomes['passed']>=0 else 5/" omega/test_runner.py
grep -q ">=0 else 5" omega/test_runner.py
git -c user.name=eval -c user.email=eval@localhost commit -q -am "baseline with planted bug"
