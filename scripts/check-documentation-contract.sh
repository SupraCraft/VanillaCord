#!/usr/bin/env bash
set -euo pipefail

required=(
  README.md
  AGENTS.md
  PROJECT_CONTRACT.json
  BRAND_PROFILE.json
  GITHUB_METADATA.json
  ARTIFACT_IDENTITY.md
  VERSIONING.md
  COMPATIBILITY_STRATEGY.md
  docs/.nojekyll
  docs/DOCUMENTATION_POLICY.md
  docs/PUBLIC_SITE_RELEASE_READINESS.md
  docs/compatibility.md
  docs/artifact-retention.md
  docs/index.html
  docs/brand-guidelines.md
  docs/assets/site.css
  docs/assets/site.js
  docs/assets/brand/icon.svg
  docs/assets/brand/hero.svg
  docs/assets/brand/brand.json
  resources/META-INF/supracraft/vanillacord/icon.svg
  scripts/apply-github-metadata.py
  scripts/build-public-site.py
  scripts/check-public-site.py
  scripts/configure-bridge-qualification.py
  package.json
  playwright.config.mjs
  lighthouserc.cjs
  tests/site/public-site.spec.mjs
  .github/workflows/compatibility.yml
  .github/workflows/documentation.yml
  .github/workflows/public-site-readiness.yml
  .github/workflows/pages.yml
)
for path in "${required[@]}"; do
  test -s "$path" || { echo "Missing required documentation/public surface: $path" >&2; exit 1; }
done

test ! -e scripts/check-public-site-browser.mjs || {
  echo 'Retired bespoke browser runner is still present.' >&2
  exit 1
}

cmp docs/assets/brand/icon.svg resources/META-INF/supracraft/vanillacord/icon.svg

python3 - <<'PY'
import json
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

contract = json.loads(Path('PROJECT_CONTRACT.json').read_text(encoding='utf-8'))
profile = json.loads(Path('BRAND_PROFILE.json').read_text(encoding='utf-8'))
metadata = json.loads(Path('GITHUB_METADATA.json').read_text(encoding='utf-8'))
brand = json.loads(Path('docs/assets/brand/brand.json').read_text(encoding='utf-8'))
package = json.loads(Path('package.json').read_text(encoding='utf-8'))
page = Path('docs/index.html').read_text(encoding='utf-8')
pages_workflow = Path('.github/workflows/pages.yml').read_text(encoding='utf-8')
readiness_workflow = Path('.github/workflows/public-site-readiness.yml').read_text(encoding='utf-8')
playwright_config = Path('playwright.config.mjs').read_text(encoding='utf-8')
lighthouse_config = Path('lighthouserc.cjs').read_text(encoding='utf-8')
browser_spec = Path('tests/site/public-site.spec.mjs').read_text(encoding='utf-8')
readiness_doc = Path('docs/PUBLIC_SITE_RELEASE_READINESS.md').read_text(encoding='utf-8')
compatibility_workflow = Path('.github/workflows/compatibility.yml').read_text(encoding='utf-8')
qualification_configurator = Path('scripts/configure-bridge-qualification.py').read_text(encoding='utf-8')

assert contract['repository'] == 'SupraCraft/VanillaCord'
assert contract['artifact']['maven'] == 'io.github.supracraft.vanillacord:vanillacord:<version>'
assert contract['artifact']['standalone'] == 'supracraft-vanillacord-<version>.jar'
assert contract['artifact']['embedded_project_icon'] == 'META-INF/supracraft/vanillacord/icon.svg'
assert 'VanillaCord.jar' in contract['artifact']['historical_aliases_forbidden_in_current_output']
assert contract['brand']['organization'] == profile['organization_brand'] == 'SupraCraft'
assert contract['brand']['contract_version'] == profile['brand_contract_version'] == brand['organization_brand']['contract_version']
assert contract['brand']['profile'] == contract['public_surface']['brand_profile'] == 'BRAND_PROFILE.json'
assert contract['brand']['runtime_dependency_on_private_repo'] is False
assert profile['snapshot_policy'] == 'vendored-reviewed-snapshot-no-private-runtime-dependency'
assert profile['identity']['cord_is_primary'] is True
assert profile['identity']['bridge_visible_in_user_identity'] is False
assert profile['packaged_resources']['source_path'] == 'resources/META-INF/supracraft/vanillacord/icon.svg'
assert contract['bridge']['user_identity_visibility'] == 'implementation-detail-not-part-of-brand'
assert contract['bridge']['release_input_policy'] == 'exact immutable coordinate'
assert contract['bridge']['consumer_qualification_workflow'] == '.github/workflows/compatibility.yml'
assert contract['bridge']['consumer_qualification_branch'] == 'qualification/bridge/<version>'
assert contract['bridge']['consumer_qualification_manifest'] == 'BRIDGE_QUALIFICATION.json'
assert contract['bridge']['consumer_qualification_configurator'] == 'scripts/configure-bridge-qualification.py'
assert contract['bridge']['consumer_qualification_evidence'] == 'build/bridge-consumer-qualification/bridge-consumer-qualification.json'
assert contract['validation']['bridge_consumer_qualification'] == '.github/workflows/compatibility.yml'
assert contract['provenance']['records_bridge_consumer_qualification_evidence'] is True
assert contract['validation']['public_site_builder'] == 'scripts/build-public-site.py'
assert contract['validation']['public_site_check'] == 'scripts/check-public-site.py'
assert contract['validation']['public_site_readiness_workflow'] == '.github/workflows/public-site-readiness.yml'
assert contract['validation']['public_site_playwright_config'] == 'playwright.config.mjs'
assert contract['validation']['public_site_browser_test'] == 'tests/site/public-site.spec.mjs'
assert contract['validation']['public_site_accessibility_engine'] == '@axe-core/playwright'
assert contract['validation']['public_site_lighthouse_config'] == 'lighthouserc.cjs'
assert contract['validation']['public_site_link_checker'] == 'lycheeverse/lychee-action'
assert contract['validation']['browser_projects'] == [
    'desktop-chromium',
    'desktop-firefox',
    'desktop-webkit',
    'android-chromium',
    'iphone-webkit',
]
assert contract['validation']['accessibility_target'] == 'WCAG 2.2 AA'
assert contract['validation']['compatibility_tiers'] == {
    'current-stable': 'blocking',
    'required-supported': 'blocking-when-requested',
    'current-development': 'advisory',
    'best-effort': 'advisory',
}
assert contract['documentation']['artifact_retention'] == 'docs/artifact-retention.md'
assert contract['documentation']['public_site_release_readiness'] == 'docs/PUBLIC_SITE_RELEASE_READINESS.md'
assert contract['public_surface']['github_metadata'] == 'GITHUB_METADATA.json'
assert contract['public_surface']['metadata_apply'] == 'scripts/apply-github-metadata.py'
assert contract['public_surface']['pages_entrypoint'] == 'docs/index.html'
assert contract['public_surface']['pages_source'] == 'github-actions'
assert contract['public_surface']['pages_workflow'] == '.github/workflows/pages.yml'
assert contract['public_surface']['site_builder'] == 'scripts/build-public-site.py'
assert contract['public_surface']['brand_manifest'] == 'docs/assets/brand/brand.json'
assert contract['public_surface']['readiness_policy'] == 'docs/PUBLIC_SITE_RELEASE_READINESS.md'
assert contract['public_surface']['human_routes']['accessibility'] == 'accessibility/'
assert contract['public_surface']['pages_url'] == metadata['homepage'] == metadata['pages']['url']
assert metadata['repository'] == contract['repository']
assert metadata['upstream_repository'] == contract['upstream_repository']
assert metadata['pages']['expected_enabled'] is True
assert metadata['pages']['source'] == 'github-actions'
assert metadata['pages']['builder'] == 'scripts/build-public-site.py'
assert metadata['pages']['workflow'] == '.github/workflows/pages.yml'
assert metadata['brand']['profile'] == 'BRAND_PROFILE.json'
assert metadata['brand']['contract_version'] == profile['brand_contract_version']
assert metadata['topics'] == sorted(set(metadata['topics']))
assert brand['project'] == 'VanillaCord'
assert brand['organization_brand']['profile_snapshot'] == 'BRAND_PROFILE.json'
assert brand['organization_brand']['runtime_dependency_on_private_repo'] is False
assert 'ME1312/VanillaCord' in page
assert 'SupraCraft/Bridge' not in page
assert metadata['homepage'] in page
assert metadata['description'] in page

for dependency in ('@playwright/test', '@axe-core/playwright', '@lhci/cli'):
    assert dependency in package['devDependencies']
    assert not package['devDependencies'][dependency].startswith(('^', '~')), f'{dependency} must be exact-pinned'
assert package['scripts']['site:test'] == 'playwright test'
assert package['scripts']['site:lighthouse'] == 'lhci autorun'

for project in contract['validation']['browser_projects']:
    assert f"name: '{project}'" in playwright_config
assert 'Pixel 5' in playwright_config
assert 'iPhone 13' in playwright_config
assert 'SITE_BASE_URL' in playwright_config
assert 'webServer: externalBaseURL' in playwright_config
assert '? undefined' in playwright_config
assert '@axe-core/playwright' in browser_spec
assert '320px reflow' in browser_spec
assert 'primary user journeys' in browser_spec
assert 'startServerCommand' in lighthouse_config
assert 'categories:accessibility' in lighthouse_config
assert 'categories:performance' in lighthouse_config

for workflow in (readiness_workflow, pages_workflow):
    for fragment in (
        'npx playwright install --with-deps chromium firefox webkit',
        'npm run site:test',
        'npm run site:lighthouse',
        'lycheeverse/lychee-action@e7477775783ea5526144ba13e8db5eec57747ce8',
    ):
        assert fragment in workflow, f'missing public-site readiness workflow contract: {fragment}'
assert 'SITE_BASE_URL: ${{ steps.deployment.outputs.page_url }}' in pages_workflow
assert '--grep "primary user journeys"' in pages_workflow
assert 'scripts/check-public-site-browser.mjs' not in readiness_doc
assert 'Playwright Test' in readiness_doc
assert 'Lighthouse CI' in readiness_doc
assert 'Lychee' in readiness_doc
assert 'WCAG 2.2 Level AA' in readiness_doc

for fragment in (
    "branches: ['qualification/bridge/**']",
    "BRIDGE_QUALIFICATION.json",
    "scripts/configure-bridge-qualification.py",
    "Bridge-Version: ${BRIDGE_VERSION}",
    "Bridge-Coordinate: io.github.supracraft.bridge:bridge:${BRIDGE_VERSION}",
    "build/bridge-consumer-qualification/bridge-consumer-qualification.json",
    '"schema": "vanillacord-bridge-consumer-qualification/1"',
    '"minecraftCompatibility": "pass"',
):
    assert fragment in compatibility_workflow, f'missing Bridge qualification workflow contract: {fragment}'
assert 'vanillacord-bridge-consumer-qualification/1' in qualification_configurator
assert 'refs/heads/qualification/bridge/{version}' in qualification_configurator
assert 'bridge-release-consumer-gate' in qualification_configurator

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
compat_retention = workflow_retention('.github/workflows/compatibility.yml', 'Upload compatibility evidence')
assert compat_retention == int(retention['actions_compatibility_report_days'])
assert compat_retention == int(retention['bridge_consumer_qualification_days'])
assert retention['release_assets'] == 'durable-historical-provenance'
assert retention['bridge_package_cleanup'] == 'owned-by-SupraCraft/Bridge-retention-policy'

with tempfile.TemporaryDirectory() as tmp:
    subprocess.run(['python3', 'scripts/build-public-site.py', '--output', tmp], check=True)
    subprocess.run(['python3', 'scripts/check-public-site.py', '--site-dir', tmp], check=True)
    out = Path(tmp)
    for name in contract['public_surface']['machine_endpoints']:
        assert (out / name).is_file(), f'missing generated endpoint: {name}'
    assert (out / contract['public_surface']['human_routes']['accessibility'] / 'index.html').is_file()
    assert json.loads((out / 'project.json').read_text()) == contract
    assert json.loads((out / 'github.json').read_text()) == metadata
    assert json.loads((out / 'brand.json').read_text()) == brand
    compatibility = json.loads((out / 'compatibility.json').read_text())
    assert compatibility['tiers'] == contract['validation']['compatibility_tiers']
    assert 'does not assert that every Minecraft version is supported' in compatibility['note']

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
  BRAND_PROFILE.json
  GITHUB_METADATA.json
  docs/compatibility.md
  docs/bridge-dependency.md
  docs/artifact-retention.md
  docs/index.html
  docs/brand-guidelines.md
  docs/PUBLIC_SITE_RELEASE_READINESS.md
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
