#!/usr/bin/env bash
set -euo pipefail

validator="scripts/validate-release-bridge-version.py"
repro="scripts/verify-reproducible-build.sh"

test -s "$validator"
test -s "$repro"
grep -F 'validate-release-bridge-version.py' "$repro" >/dev/null

python3 "$validator" 0.1.0 >/dev/null
python3 "$validator" 12.34.56-rc.1 >/dev/null
python3 "$validator" 12.34.56-rc.27 >/dev/null

invalid=(
  '0.1.1-dev.107'
  '0.1.0-dev'
  '0.1.0-rc.0'
  '0.1.0-SNAPSHOT'
  'latest'
  'v0.1.0'
  ''
)
for version in "${invalid[@]}"; do
  if python3 "$validator" "$version" >/dev/null 2>&1; then
    echo "Release Bridge validator unexpectedly accepted: '$version'" >&2
    exit 1
  fi
done

python3 - <<'PY'
import json
from pathlib import Path

contract = json.loads(Path('PROJECT_CONTRACT.json').read_text(encoding='utf-8'))
assert contract['bridge']['release_input_policy'] == 'exact immutable release-candidate or stable coordinate'

versioning = Path('VERSIONING.md').read_text(encoding='utf-8')
assert 'X.Y.Z-rc.N` or stable `X.Y.Z` Bridge coordinate' in versioning
assert 'X.Y.Z-dev.N` Bridge coordinate is rejected for release work' in versioning
PY

printf 'Release Bridge input policy OK\n'
