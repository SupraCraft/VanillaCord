#!/usr/bin/env bash
set -uo pipefail

if [[ $# -gt 0 ]]; then
  JAR_PATH="$1"
else
  mapfile -t canonical_jars < <(find artifacts -maxdepth 1 -type f -name 'supracraft-vanillacord-*.jar' -print | LC_ALL=C sort)
  if [[ ${#canonical_jars[@]} -ne 1 ]]; then
    echo "Expected exactly one canonical SupraCraft VanillaCord jar in artifacts/, found ${#canonical_jars[@]}." >&2
    printf '%s\n' "${canonical_jars[@]}" >&2
    exit 1
  fi
  JAR_PATH="${canonical_jars[0]}"
fi

MANIFEST_URL="${MINECRAFT_MANIFEST_URL:-https://piston-meta.mojang.com/mc/game/version_manifest_v2.json}"
REQUIRED_SUPPORTED="${VANILLACORD_REQUIRED_SUPPORTED-1.21.11 1.20.6 1.20.4 1.19.4 1.18.2}"
BEST_EFFORT_LEGACY="${VANILLACORD_BEST_EFFORT_LEGACY-1.17.1 1.16.5 1.12.2 1.8.9 1.7.10}"
INCLUDE_SNAPSHOT="${VANILLACORD_INCLUDE_SNAPSHOT:-true}"
BOOT_SMOKE="${VANILLACORD_BOOT_SMOKE:-false}"
BOOT_TIMEOUT_SECONDS="${VANILLACORD_BOOT_TIMEOUT_SECONDS:-120}"
REPORT_PATH="${VANILLACORD_COMPAT_REPORT:-docs/minecraft-compatibility-report.md}"

if [[ "$REQUIRED_SUPPORTED" == "none" || "$REQUIRED_SUPPORTED" == "-" ]]; then
  REQUIRED_SUPPORTED=""
fi
if [[ "$BEST_EFFORT_LEGACY" == "none" || "$BEST_EFFORT_LEGACY" == "-" ]]; then
  BEST_EFFORT_LEGACY=""
fi
if [[ ! -f "$JAR_PATH" ]]; then
  echo "VanillaCord jar not found: $JAR_PATH" >&2
  exit 1
fi

manifest_json="$(python3 - "$MANIFEST_URL" <<'PY'
import sys
from urllib.request import urlopen
with urlopen(sys.argv[1], timeout=30) as response:
    sys.stdout.write(response.read().decode("utf-8"))
PY
)"
manifest_file="$(mktemp)"
trap 'rm -f "$manifest_file"' EXIT
printf '%s' "$manifest_json" > "$manifest_file"

latest_release="$(python3 - "$manifest_file" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as handle:
    manifest = json.load(handle)
print(manifest["latest"]["release"])
PY
)"
latest_snapshot="$(python3 - "$manifest_file" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as handle:
    manifest = json.load(handle)
print(manifest["latest"]["snapshot"])
PY
)"

version_exists() {
  local version="$1"
  python3 - "$manifest_file" "$version" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as handle:
    manifest = json.load(handle)
version = sys.argv[2]
sys.exit(0 if any(item["id"] == version for item in manifest["versions"]) else 1)
PY
}

append_unique() {
  local list="$1" value="$2"
  if [[ " $list " == *" $value "* ]]; then
    printf '%s\n' "$list"
  else
    printf '%s %s\n' "$list" "$value"
  fi
}

blocking_versions="$latest_release"
for version in $REQUIRED_SUPPORTED; do
  blocking_versions="$(append_unique "$blocking_versions" "$version")"
done

current_development=""
if [[ "$INCLUDE_SNAPSHOT" == "true" && -n "$latest_snapshot" && "$latest_snapshot" != "$latest_release" ]]; then
  current_development="$latest_snapshot"
fi

legacy_versions=""
for version in $BEST_EFFORT_LEGACY; do
  legacy_versions="$(append_unique "$legacy_versions" "$version")"
done

{
  mkdir -p "$(dirname "$REPORT_PATH")"
  echo "# VanillaCord Minecraft Compatibility Report"
  echo
  echo "- Generated: \`$(date -u +%Y-%m-%dT%H:%M:%SZ)\`"
  echo "- Manifest: \`$MANIFEST_URL\`"
  echo "- Latest release: \`$latest_release\`"
  echo "- Latest snapshot: \`$latest_snapshot\`"
  echo "- Jar: \`$JAR_PATH\`"
  echo "- Required supported matrix: \`$REQUIRED_SUPPORTED\`"
  echo "- Best-effort legacy matrix: \`$BEST_EFFORT_LEGACY\`"
  echo "- Include current development: \`$INCLUDE_SNAPSHOT\`"
  echo "- Boot latest stable: \`$BOOT_SMOKE\`"
  echo "- Policy: current-stable/required-supported failures are blocking; current-development/best-effort failures are advisory."
  echo
  echo "| Tier | Version | Policy | Result |"
  echo "| --- | --- | --- | --- |"
} > "$REPORT_PATH"

blocking_failed=0
advisory_failed=0

record_failure() {
  local blocking="$1"
  if [[ "$blocking" == "true" ]]; then
    blocking_failed=1
  else
    advisory_failed=1
  fi
}

boot_smoke() {
  local version="$1" output_jar="$2" workdir pid elapsed=0
  workdir="$(mktemp -d)"
  cp "$output_jar" "$workdir/server.jar"
  printf 'eula=true\n' > "$workdir/eula.txt"
  cat > "$workdir/server.properties" <<'EOF'
online-mode=false
enforce-secure-profile=false
server-ip=127.0.0.1
server-port=25565
motd=VanillaCord compatibility smoke test
level-name=world
view-distance=2
simulation-distance=2
spawn-protection=0
EOF

  mkfifo "$workdir/server.in"
  exec 9<>"$workdir/server.in"
  (
    cd "$workdir" || exit 1
    java -Xms256M -Xmx1536M -jar server.jar nogui <&9 >server.log 2>&1
  ) &
  pid=$!

  while (( elapsed < BOOT_TIMEOUT_SECONDS )); do
    if grep -Eq 'Done \([^)]*\)!|Done \(' "$workdir/server.log" 2>/dev/null; then
      printf 'stop\n' >&9 || true
      for _ in $(seq 1 30); do
        if ! kill -0 "$pid" 2>/dev/null; then break; fi
        sleep 1
      done
      if kill -0 "$pid" 2>/dev/null; then kill "$pid" 2>/dev/null || true; fi
      wait "$pid" 2>/dev/null || true
      exec 9>&-
      rm -rf "$workdir"
      return 0
    fi
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "Minecraft $version exited before reaching the startup marker." >&2
      tail -n 80 "$workdir/server.log" >&2 || true
      wait "$pid" 2>/dev/null || true
      exec 9>&-
      rm -rf "$workdir"
      return 1
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done

  echo "Minecraft $version did not reach the startup marker within ${BOOT_TIMEOUT_SECONDS}s." >&2
  tail -n 80 "$workdir/server.log" >&2 || true
  printf 'stop\n' >&9 || true
  sleep 2
  kill "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
  exec 9>&-
  rm -rf "$workdir"
  return 1
}

run_probe() {
  local tier="$1" version="$2" blocking="$3"
  local policy="advisory"
  local output_jar="out/${version}.jar"
  [[ "$blocking" == "true" ]] && policy="blocking"

  if ! version_exists "$version"; then
    echo "| $tier | \`$version\` | $policy | missing from Mojang manifest |" >> "$REPORT_PATH"
    record_failure "$blocking"
    return
  fi

  rm -f "$output_jar"
  echo "Patching Minecraft $version ($tier, $policy)"
  if ! java -jar "$JAR_PATH" "$version"; then
    echo "| $tier | \`$version\` | $policy | patch failed |" >> "$REPORT_PATH"
    record_failure "$blocking"
    return
  fi
  if [[ ! -s "$output_jar" ]]; then
    echo "| $tier | \`$version\` | $policy | patch exited successfully but output jar is missing/empty |" >> "$REPORT_PATH"
    record_failure "$blocking"
    return
  fi
  if ! jar tf "$output_jar" >/dev/null 2>&1; then
    echo "| $tier | \`$version\` | $policy | patched output is not a readable jar |" >> "$REPORT_PATH"
    record_failure "$blocking"
    return
  fi

  if [[ "$BOOT_SMOKE" == "true" && "$version" == "$latest_release" ]]; then
    echo "Booting patched Minecraft $version"
    if ! boot_smoke "$version" "$output_jar"; then
      echo "| $tier | \`$version\` | $policy | boot smoke failed |" >> "$REPORT_PATH"
      record_failure "$blocking"
      return
    fi
    echo "| $tier | \`$version\` | $policy | pass (patch + jar integrity + boot) |" >> "$REPORT_PATH"
    return
  fi

  echo "| $tier | \`$version\` | $policy | pass (patch + jar integrity) |" >> "$REPORT_PATH"
}

run_probe "current-stable" "$latest_release" "true"

for version in $REQUIRED_SUPPORTED; do
  if [[ "$version" != "$latest_release" ]]; then
    run_probe "required-supported" "$version" "true"
  fi
done

if [[ -n "$current_development" ]]; then
  run_probe "current-development" "$current_development" "false"
fi

for version in $legacy_versions; do
  run_probe "best-effort" "$version" "false"
done

echo
cat "$REPORT_PATH"

if [[ "$advisory_failed" -ne 0 ]]; then
  echo "One or more advisory compatibility targets failed. Stable/release gating remains unaffected; see $REPORT_PATH." >&2
fi
if [[ "$blocking_failed" -ne 0 ]]; then
  echo "One or more blocking Minecraft compatibility targets failed. See $REPORT_PATH." >&2
  exit 1
fi
