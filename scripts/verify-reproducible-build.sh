#!/usr/bin/env bash
set -euo pipefail

version="${1:?VanillaCord version is required}"
bridge_owner="${2:?Bridge owner is required}"
bridge_version="${3:?exact Bridge version is required}"
build_commit="${4:?build commit is required}"
build_ref="${5:?build ref is required}"
build_number="${6:?build number is required}"

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

build_once() {
  local label="$1"
  local expected="artifacts/supracraft-vanillacord-${version}.jar"

  rm -rf build artifacts
  ./mvnw -B clean verify \
    -Dbridge.owner="${bridge_owner}" \
    -Dbridge.version="${bridge_version}" \
    -Dbuild.commit="${build_commit}" \
    -Dbuild.ref="${build_ref}" \
    -Dbuild.number="${build_number}"

  test -s "$expected"
  cp "$expected" "$tmpdir/${label}.jar"
  unzip -l "$expected" > "$tmpdir/${label}.entries.txt"
  zipinfo -l "$expected" > "$tmpdir/${label}.zipinfo.txt"
  sha256sum "$expected" | tee "$tmpdir/${label}.sha256"
}

build_once first
build_once second

first_hash="$(cut -d' ' -f1 "$tmpdir/first.sha256")"
second_hash="$(cut -d' ' -f1 "$tmpdir/second.sha256")"

if ! cmp -s "$tmpdir/first.jar" "$tmpdir/second.jar"; then
  echo "Reproducibility failure: canonical JAR bytes differ." >&2
  echo "first:  $first_hash" >&2
  echo "second: $second_hash" >&2
  echo "Entry-list diff:" >&2
  diff -u "$tmpdir/first.entries.txt" "$tmpdir/second.entries.txt" >&2 || true
  echo "ZIP metadata diff:" >&2
  diff -u "$tmpdir/first.zipinfo.txt" "$tmpdir/second.zipinfo.txt" >&2 || true
  mkdir -p reproducibility-diagnostics
  cp "$tmpdir"/*.txt "$tmpdir"/*.sha256 reproducibility-diagnostics/
  exit 1
fi

printf 'reproducible.sha256=%s\n' "$first_hash" > REPRODUCIBILITY.properties
printf 'reproducible.version=%s\n' "$version" >> REPRODUCIBILITY.properties
printf 'reproducible.bridge.version=%s\n' "$bridge_version" >> REPRODUCIBILITY.properties

# The second clean build remains in artifacts/ so downstream contract/checksum
# steps operate on an artifact already proven byte-identical to the first build.
echo "Reproducible canonical JAR: $first_hash"
