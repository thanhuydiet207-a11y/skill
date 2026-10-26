#!/usr/bin/env bash
# Copy the ledger fixture (no OMEGA files, so the no-plugin arm is a clean baseline) and commit it.
set -euo pipefail
cp -R "$(dirname "$0")/../fixtures/ledger/." .
[ -d .git ] || git init -q
git add -A
git -c user.name=eval -c user.email=eval@localhost commit -q -m baseline
