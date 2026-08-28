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
  docs/brand-guidelines.md
  docs/index.html
  docs/assets/brand/brand.json
  docs/assets/brand/icon.svg
  docs/assets/brand/hero.svg
  src/main/resources/META-INF/supracraft/vanillacord/icon.svg
  src/main/resources/META-INF/supracraft/vanillacord/icon-128.png
  scripts/apply-github-metadata.py
  scripts/build-public-site.py
  .github/workflows/pages.yml
)
for path in "${required[@]}"; do
  test -s "$path" || { echo "Missing required documentation/public surface: $path" >&2; exit 1; }
done

python3 - <<'PY'
import json
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

contract = json.loads(Path('PROJECT_CONTRACT.json').read_text(encoding='utf-8'))
metadata = json.loads(Path('GITHUB_METADATA.json').read_text(encoding='utf-8'))
brand = json.loads(Path('docs/assets/brand/brand.json').read_text(encoding='utf-8'))
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
assert contract['documentation']['brand_guidelines'] == 'docs/brand-guidelines.md'
assert contract['branding']['organization'] == brand['organization'] == 'SupraCraft'
assert contract['branding']['organization_contract_version'] == brand['organization_brand_contract'] == metadata['brand']['organization_contract']
assert contract['branding']['family'] == brand['family'] == 'minecraft-server'
assert contract['bridge']['user_facing_brand_role'] == 'implementation-detail'
assert contract['public_surface']['github_metadata'] == 'GITHUB_METADATA.json'
assert contract['public_surface']['metadata_apply'] == 'scripts/apply-github-metadata.py'
assert contract['public_surface']['pages_entrypoint'] == 'docs/index.html'
assert contract['public_surface']['pages_builder'] == metadata['pages']['builder'] == 'scripts/build-public-site.py'
assert contract['public_surface']['pages_workflow'] == metadata['pages']['workflow'] == '.github/workflows/pages.yml'
assert contract['public_surface']['pages_url'] == metadata['homepage'] == metadata['pages']['url']
assert contract['public_surface']['machine_endpoints'] == ['project.json', 'github.json', 'brand.json', 'artifacts.json', 'compatibility.json', 'llms.txt']
assert metadata['repository'] == contract['repository']
assert metadata['upstream_repository'] == contract['upstream_repository']
assert metadata['pages']['expected_enabled'] is True
assert metadata['pages']['source'] == 'github-actions'
assert metadata['topics'] == sorted(set(metadata['topics']))
assert 'ME1312/VanillaCord' in page
assert metadata['homepage'] in page
assert metadata['description'] in page
assert 'SupraCraft/Bridge' not in page, 'Bridge is an implementation detail and should not be featured on the public landing page'
assert 'Connect vanilla Minecraft servers to proxies with forwarded player identity.' in page
assert 'assets/brand/icon.svg' in page and 'assets/brand/hero.svg' in page

web_icon = Path('docs/assets/brand/icon.svg').read_bytes()
jar_icon = Path('src/main/resources/META-INF/supracraft/vanillacord/icon.svg').read_bytes()
assert web_icon == jar_icon, 'web and JAR SVG icon masters diverged'

png = Path('src/main/resources/META-INF/supracraft/vanillacord/icon-128.png').read_bytes()
assert png[:8] == b'\x89PNG\r\n\x1a\n'
width, height = struct.unpack('>II', png[16:24])
assert (width, height) == (128, 128)

root = ET.parse('pom.xml').getroot()
ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
def text(path):
    node = root.find(path, ns)
    assert node is not None and node.text
    return node.text.strip()

assert contract['source_version'] == text('m:version')
assert int(contract['toolchain']['java_bytecode_release']) == int(text('m:properties/m:maven.compiler.release'))
resource_dirs = [node.text.strip() for node in root.findall('m:build/m:resources/m:resource/m:directory', ns) if node.text]
assert 'src/main/resources' in resource_dirs

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

for path in [Path('README.md'), Path('AGENTS.md'), Path('docs/compatibility.md'), Path('docs/bridge-dependency.md')]:
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if 'artifacts/VanillaCord.jar' in line:
            lowered = line.lower()
            assert ('do not use' in lowered or 'historical' in lowered or 'retired' in lowered), \
                f'{path}:{number}: retired VanillaCord.jar path used as current instruction'
PY

site_dir="$(mktemp -d)"
trap 'rm -rf "$site_dir"' EXIT
python3 scripts/build-public-site.py --output "$site_dir"
for path in index.html project.json github.json brand.json artifacts.json compatibility.json llms.txt assets/brand/icon.svg assets/brand/hero.svg; do
  test -s "$site_dir/$path" || { echo "Public-site build omitted $path" >&2; exit 1; }
done

active_docs=(
  README.md
  AGENTS.md
  PROJECT_CONTRACT.json
  GITHUB_METADATA.json
  docs/compatibility.md
  docs/bridge-dependency.md
  docs/artifact-retention.md
  docs/brand-guidelines.md
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

printf 'Documentation/public-surface contract OK\n'
