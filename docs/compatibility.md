# VanillaCord compatibility operations

This guide explains how humans, automation, and agents should run the compatibility sentinel. Policy rationale lives in `../COMPATIBILITY_STRATEGY.md`; this file describes the executable interface.

## Canonical probe

The compatibility implementation is:

```sh
scripts/check-minecraft-compatibility.sh
```

If no JAR path is supplied, the script requires exactly one canonical artifact matching:

```text
artifacts/supracraft-vanillacord-*.jar
```

An explicit canonical JAR path may also be passed as the first argument. Do not use the retired `artifacts/VanillaCord.jar` name.

## Tier policy

| Tier | Source | Routine policy | Exit-code effect |
| --- | --- | --- | --- |
| `current-stable` | latest Mojang stable from `version_manifest_v2.json` | patch + integrity; boot when enabled | blocking |
| `current-development` | latest snapshot/RC/pre-release when enabled | patch + integrity | advisory |
| `required-supported` | explicit maintained versions | when requested | blocking |
| `best-effort` | explicit historical versions | when requested | advisory |

A development snapshot failure is early-warning evidence. It does not independently fail the command when all blocking targets pass.

Default maintained fixtures in the script are currently:

```text
required-supported: 1.21.11 1.20.6 1.20.4 1.19.4 1.18.2
best-effort:        1.17.1 1.16.5 1.12.2 1.8.9 1.7.10
```

These defaults are executable configuration, not a promise that every historical target receives routine validation.

## Environment controls

```sh
VANILLACORD_INCLUDE_SNAPSHOT=false
VANILLACORD_REQUIRED_SUPPORTED="1.21.11 1.20.6"
VANILLACORD_BEST_EFFORT_LEGACY="1.16.5 1.12.2"
VANILLACORD_BOOT_SMOKE=true
VANILLACORD_BOOT_TIMEOUT_SECONDS=120
VANILLACORD_COMPAT_REPORT=/tmp/vanillacord-compatibility.md
```

Set either version-list variable to an empty string, `none`, or `-` to clear that tier for a focused smoke run.

## Build before probing

Use the pinned Maven Wrapper, not a system Maven:

```sh
export BRIDGE_OWNER="${BRIDGE_OWNER:-SupraCraft}"
export BRIDGE_VERSION="${BRIDGE_VERSION:-$(./scripts/resolve-bridge-version.sh)}"
./mvnw -B verify -Dbridge.version="$BRIDGE_VERSION"
```

CI records the exact resolved Bridge coordinate. For reproducibility/release investigation, set `BRIDGE_VERSION` to the exact previously recorded version instead of resolving again.

GitHub Packages access normally requires `GITHUB_TOKEN`/`GITHUB_ACTOR` credentials with package-read access.

## Local compatibility run

On a Unix-like environment with the required Java/Python/Bash tools available:

```sh
export VANILLACORD_BOOT_SMOKE=true
scripts/check-minecraft-compatibility.sh
```

On Windows, the repository PowerShell wrapper may be used. The Docker mode supplies the compatibility runtime environment while the repository build itself remains wrapper-driven:

```powershell
$env:GITHUB_TOKEN = (gh auth token).Trim()
.\scripts\Invoke-CompatibilityProbe.ps1 -UseDocker
```

For a cheap current-stable-only smoke:

```powershell
$env:GITHUB_TOKEN = (gh auth token).Trim()
.\scripts\Invoke-CompatibilityProbe.ps1 -UseDocker -SkipSnapshot -RequiredSupported "" -BestEffortLegacy ""
```

## GitHub Actions behavior

`.github/workflows/compatibility.yml` provides three operating modes:

- pull-request validation: narrowly proves current stable for compatibility-harness changes;
- scheduled sentinel: current stable is blocking and development Minecraft is advisory;
- manual dispatch: permits explicit maintained/legacy version sets and boot controls.

The workflow report is appended to the job summary and uploaded as a workflow artifact. Treat that workflow evidence as the authoritative current run result.

## Repository report file

`docs/minecraft-compatibility-report.md` is not a continuously updated status page. It is a repository-held note explaining where authoritative current compatibility evidence lives. Probe runs may write a generated report to another path via `VANILLACORD_COMPAT_REPORT`; do not commit transient output as though it were evergreen project documentation.

## Automation contract

Automation should parse the generated report's `Tier`, `Version`, `Policy`, and `Result` columns rather than infer policy from version names. It should also use the process exit code for the aggregate blocking result.

Do not duplicate Minecraft-version resolution or tier semantics in another script unless a concrete integration requires it; call the canonical probe instead.
