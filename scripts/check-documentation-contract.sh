#!/usr/bin/env bash
set -euo pipefail

required=(
  README.md
  AGENTS.md
  PROJECT_CONTRACT.json
  GITHUB_METADATA.json
  ARTIFACT_IDENTITY.md
  VERSIONING.md
  COMPATIBILITY_STRATEGY.md
  docs/.nojekyll
  docs/DOCUMENTATION_POLICY.md
  docs/compatibility.md
  docs/artifact-retention.md
  docs/index.html
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
metadata = json.loads(Path('GITHUB_METADATA.json').read_text(encoding='utf-8'))
page = Path('docs/index.html').read_text(encoding='utf-8')

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
assert contract['documentation']['artifact_retention'] == 'docs/artifact-retention.md'
assert contract['public_surface']['github_metadata'] == 'GITHUB_METADATA.json'
assert contract['public_surface']['pages_entrypoint'] == 'docs/index.html'
assert contract['public_surface']['pages_url'] == metadata['homepage'] == metadata['pages']['url']
assert metadata['repository'] == contract['repository']
assert metadata['upstream_repository'] == contract['upstream_repository']
assert metadata['pages']['expected_enabled'] is True
assert metadata['pages']['source'] == 'branch'
assert metadata['pages']['branch'] == 'master'
assert metadata['pages']['content_root'] == 'docs/'
assert metadata['topics'] == sorted(set(metadata['topics']))
assert 'ME1312/VanillaCord' in page
assert 'SupraCraft/Bridge' in page
assert metadata['homepage'] in page
assert metadata['description'] in page

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

def workflow_retention(path, step_name):
    workflow = Path(path).read_text(encoding='utf-8')
    step = re.search(
        rf'- name: {re.escape(step_name)}(?P<body>.*?)(?=\n\s+- name:|\Z)',
        workflow,
        re.DOTALL,
    )
    assert step, f'{path}: missing step {step_name!r}'
    retention = re.search(r'retention-days:\s*(\d+)', step.group('body'))
    assert retention, f'{path}: step {step_name!r} has no retention-days'
    return int(retention.group(1))

retention = contract['retention']
assert workflow_retention('.github/workflows/build.yml', 'Upload reproducibility diagnostics on failure') == int(retention['actions_reproducibility_diagnostics_days'])
assert workflow_retention('.github/workflows/build.yml', 'Upload build evidence') == int(retention['actions_build_evidence_days'])
assert workflow_retention('.github/workflows/compatibility.yml', 'Upload compatibility report') == int(retention['actions_compatibility_report_days'])
assert retention['release_assets'] == 'durable-historical-provenance'
assert retention['bridge_package_cleanup'] == 'owned-by-SupraCraft/Bridge-retention-policy'

# The retired path may appear only in an explicit negative/historical warning.
for path in [Path('README.md'), Path('AGENTS.md'), Path('docs/compatibility.md'), Path('docs/bridge-dependency.md')]:
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if 'artifacts/VanillaCord.jar' in line:
            lowered = line.lower()
            assert ('do not use' in lowered or 'historical' in lowered or 'retired' in lowered), \
                f'{path}:{number}: retired VanillaCord.jar path used as current instruction'
PY

active_docs=(
  README.md
  AGENTS.md
  PROJECT_CONTRACT.json
  GITHUB_METADATA.json
  docs/compatibility.md
  docs/bridge-dependency.md
  docs/artifact-retention.md
  docs/index.html
)

if grep -nHE '0\.1\.0-dev\.[0-9]+' "${active_docs[@]}"; then
  echo 'Volatile concrete Bridge development coordinate reappeared in evergreen documentation.' >&2
  exit 1
fi

if grep -nH -F 'BRIDGE_OWNER:-mark-e-deyoung' "${active_docs[@]}"; then
  echo 'Personal Bridge owner default reappeared in evergreen documentation.' >&2
  exit 1
fi

printf 'Documentation contract OK\n'
