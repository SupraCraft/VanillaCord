#!/usr/bin/env bash
set -euo pipefail

jar_path="${1:-artifacts/VanillaCord.jar}"
expected_version="${2:?expected VanillaCord version is required}"
expected_bridge="${3:?expected Bridge version is required}"
expected_commit="${4:-}"
inventory_path="${5:-ARTIFACT-INVENTORY.txt}"

fail() {
  echo "artifact contract failure: $*" >&2
  exit 1
}

[[ -s "$jar_path" ]] || fail "missing or empty JAR: $jar_path"
jar tf "$jar_path" >/tmp/vanillacord-jar-entries.txt || fail "JAR is unreadable"
LC_ALL=C sort /tmp/vanillacord-jar-entries.txt >"$inventory_path"

require_entry() { grep -Fxq "$1" /tmp/vanillacord-jar-entries.txt || fail "required JAR entry missing: $1"; }
forbid_entry() { if grep -Fxq "$1" /tmp/vanillacord-jar-entries.txt; then fail "provided dependency leaked into fat JAR: $1"; fi; }

require_entry 'vanillacord/Downloader.class'
require_entry 'com/alibaba/fastjson2/JSON.class'
require_entry 'org/objectweb/asm/ClassReader.class'
require_entry 'LICENSE'
forbid_entry 'com/mojang/authlib/GameProfile.class'
forbid_entry 'io/netty/buffer/ByteBuf.class'

unzip -p "$jar_path" META-INF/MANIFEST.MF | tr -d '\r' >/tmp/vanillacord-manifest.mf \
  || fail "cannot read generated manifest"

require_manifest() {
  grep -Fqx "$1" /tmp/vanillacord-manifest.mf || fail "manifest contract changed or missing: $1"
}

require_manifest 'Main-Class: vanillacord.Downloader'
require_manifest 'Implementation-Title: VanillaCord'
require_manifest 'Implementation-Vendor: SupraCraft'
require_manifest "Implementation-Version: ${expected_version}"
require_manifest 'Source-Repository: SupraCraft/VanillaCord'
require_manifest 'Upstream-Repository: ME1312/VanillaCord'
require_manifest "Bridge-Version: ${expected_bridge}"
require_manifest "Bridge-Coordinate: io.github.supracraft.bridge:bridge:${expected_bridge}"

if [[ -n "$expected_commit" ]]; then
  require_manifest "Build-Commit: ${expected_commit}"
fi

echo "Artifact contract verified: $jar_path"
echo "Inventory: $inventory_path"
