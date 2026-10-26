#!/usr/bin/env bash
# Copy the slug fixture into the workspace and commit it as the baseline.
set -euo pipefail
cp -R "$(dirname "$0")/../fixtures/slug/." .
[ -d .git ] || git init -q
git add -A
git -c user.name=eval -c user.email=eval@localhost commit -q -m baseline
