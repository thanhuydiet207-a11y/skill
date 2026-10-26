#!/usr/bin/env bash
# Copy the committed OMEGA checkout (plus pinned TypeScript dev tools) into the eval workspace and commit it as a baseline.
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
git -C "$repo" archive HEAD | tar -x
if [ -d "$repo/integration/typescript/node_modules" ]; then cp -R "$repo/integration/typescript/node_modules" integration/typescript/; fi
[ -d .git ] || git init -q
git add -A
git -c user.name=eval -c user.email=eval@localhost commit -q -m baseline
