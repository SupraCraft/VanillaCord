#!/usr/bin/env bash
set -euo pipefail

# Resolve the newest immutable SupraCraft Bridge development build from GitHub Packages.
# Requires a token with read:packages. Exact BRIDGE_VERSION pins remain preferred when
# reproducibility matters; this resolver is for normal integration CI.

ROOT="${BASH_SOURCE%/*}/.."
cd "$ROOT"

BRIDGE_OWNER="${BRIDGE_OWNER:-${GITHUB_REPOSITORY_OWNER:-SupraCraft}}"
TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
ACTOR="${GITHUB_ACTOR:-token}"

if [[ -z "${TOKEN}" ]]; then
  echo "GITHUB_TOKEN (or GH_TOKEN) is required to read Bridge artifacts from GitHub Packages." >&2
  exit 1
fi

META_URL="https://maven.pkg.github.com/${BRIDGE_OWNER}/Bridge/io/github/supracraft/bridge/bridge/maven-metadata.xml"
xml="$(curl -fsSL -u "${ACTOR}:${TOKEN}" "${META_URL}")"

version="$(
  XML_CONTENT="$xml" python3 - <<'PY'
import os
import re
import sys
import xml.etree.ElementTree as ET

root = ET.fromstring(os.environ["XML_CONTENT"])
versions = [
    node.text.strip()
    for node in root.findall("./versioning/versions/version")
    if node.text and node.text.strip()
]

# Development integration uses only immutable X.Y.Z-dev.N builds. Do not
# accidentally select historical SNAPSHOT coordinates, release candidates,
# or stable releases merely because repository metadata calls them latest.
pattern = re.compile(r"^(\d+)\.(\d+)\.(\d+)-dev\.(\d+)$")
candidates = []
for value in versions:
    match = pattern.fullmatch(value)
    if match:
        candidates.append((tuple(map(int, match.groups())), value))

if not candidates:
    sys.exit("No canonical Bridge X.Y.Z-dev.N versions found in GitHub Packages")

print(max(candidates)[1])
PY
)"

echo "${version}"
