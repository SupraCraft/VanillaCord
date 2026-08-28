#!/usr/bin/env bash
set -euo pipefail

required=(
  README.md
  AGENTS.md
  PROJECT_CONTRACT.json
  ARTIFACT_IDENTITY.md
  VERSIONING.md
  COMPATIBILITY_STRATEGY.md
  docs/DOCUMENTATION_POLICY.md
  docs/compatibility.md
)
for path in "${required[@]}"; do
  test -s "$path" || { echo "Missing required documentation surface: $path" >&2; exit 1; }
done

python3 - <<'PY'
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

contract = json.loads(Path('PROJECT_CONTRACT.json').read_text(encoding='utf-8'))
assert contract['repository'] == 'SupraCraft/VanillaCord'
assert contract['artifact']['maven'] == 'io.github.supracraft.vanillacord:vanillacord:<version>'
assert contract['artifact']['standalone'] == 'supracraft-vanillacord-<version>.jar'
assert 'VanillaCord.jar' in contract['artifact']['historical_aliases_forbidden_in_current_output']
assert contract['validation']['compatibility_tiers'] == {
    'current-stable': 'blocking',
    'required-supported': 'blocking-when-requested',
    'current-development': 'advisory',
    'best-effort': 'advisory',
}

root = ET.parse('pom.xml').getroot()
ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
def text(path):
    node = root.find(path, ns)
    assert node is not None and node.text
    return node.text.strip()

assert contract['source_version'] == text('m:version')
assert int(contract['toolchain']['java_bytecode_release']) == int(text('m:properties/m:maven.compiler.release'))

wrapper = Path('.mvn/wrapper/maven-wrapper.properties').read_text(encoding='utf-8')
match = re.search(r'apache-maven-([0-9.]+)-bin', wrapper)
assert match, 'Unable to determine Maven version from wrapper properties'
assert contract['toolchain']['maven'] == match.group(1)
PY

active_docs=(
  README.md
  AGENTS.md
  PROJECT_CONTRACT.json
  docs/compatibility.md
  docs/bridge-dependency.md
)

if grep -nH -F 'artifacts/VanillaCord.jar' "${active_docs[@]}"; then
  echo 'Retired VanillaCord.jar operational path reappeared in evergreen documentation.' >&2
  exit 1
fi

if grep -nHE '0\.1\.0-dev\.[0-9]+' "${active_docs[@]}"; then
  echo 'Volatile concrete Bridge development coordinate reappeared in evergreen documentation.' >&2
  exit 1
fi

if grep -nH -F 'BRIDGE_OWNER:-mark-e-deyoung' "${active_docs[@]}"; then
  echo 'Personal Bridge owner default reappeared in evergreen documentation.' >&2
  exit 1
fi

printf 'Documentation contract OK\n'
