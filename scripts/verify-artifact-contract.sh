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

require_entry() {
  grep -Fxq "$1" /tmp/vanillacord-jar-entries.txt || fail "required JAR entry missing: $1"
}

forbid_entry() {
  if grep -Fxq "$1" /tmp/vanillacord-jar-entries.txt; then
    fail "provided dependency leaked into fat JAR: $1"
  fi
}

require_entry 'vanillacord/Downloader.class'
require_entry 'com/alibaba/fastjson2/JSON.class'
require_entry 'org/objectweb/asm/ClassReader.class'
require_entry 'LICENSE'

forbid_entry 'com/mojang/authlib/GameProfile.class'
forbid_entry 'io/netty/buffer/ByteBuf.class'

unzip -p "$jar_path" META-INF/MANIFEST.MF >/tmp/vanillacord-manifest.mf \
  || fail "cannot read generated manifest"

grep -Fqx 'Main-Class: vanillacord.Downloader' /tmp/vanillacord-manifest.mf \
  || fail 'main class manifest contract changed'
grep -Fqx "Implementation-Version: ${expected_version}" /tmp/vanillacord-manifest.mf \
  || fail 'implementation version does not match effective build version'
grep -Fqx "Bridge-Version: ${expected_bridge}" /tmp/vanillacord-manifest.mf \
  || fail 'Bridge provenance does not match resolved build input'

if [[ -n "$expected_commit" ]]; then
  grep -Fqx "Build-Commit: ${expected_commit}" /tmp/vanillacord-manifest.mf \
    || fail 'source commit provenance does not match build input'
fi

echo "Artifact contract verified: $jar_path"
echo "Inventory: $inventory_path"
