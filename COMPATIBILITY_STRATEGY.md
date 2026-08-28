# Minecraft Compatibility Strategy

Last reviewed: 2026-08-28

## Purpose

VanillaCord is a bytecode patcher that discovers obfuscated Minecraft server classes at patch time. Compatibility assurance should answer one question with the least machinery necessary:

> Does the current VanillaCord build still patch and operate against the Minecraft versions that matter?

The strategy deliberately favors deterministic, stateless checks over a compatibility-management service. The monitor observes and reports; it does not modify VanillaCord code automatically.

## Current Architecture

- `Downloader` reads Mojang's `version_manifest_v2.json`, downloads a requested server jar, verifies Mojang's SHA-1 metadata, and patches it.
- `Patcher` distinguishes modern bundled server jars from older fat jars by checking `Bundler-Format` in `META-INF/MANIFEST.MF`.
- `SourceScanner` discovers patch targets using string and structural signals.
- Login extension support contains version-era handling for older mutable packet classes, constructor-based packets, and modern record/interface packet shapes.
- Current Minecraft compatibility probes run with JDK 25; VanillaCord emits Java 21 bytecode for its own classes.

## Red-Team Decision

The project maintains a **compatibility sentinel**, not a compatibility platform.

High-value automation:

- periodically resolve Mojang's latest stable and snapshot/RC;
- build VanillaCord and patch those current versions;
- preserve a human-readable compatibility report and workflow diagnostics;
- keep current stable blocking and development snapshots advisory;
- retain a manually triggered maintained/legacy matrix for regressions;
- use patch-output integrity, boot, forwarding-boundary, and scanner tests where they catch real failure modes;
- prefer stronger scanner evidence without replacing compatibility fallbacks.

Explicit non-goals unless future evidence justifies them include autonomous repair, persistent compatibility databases, automatic issue churn for transient probes, daily full-history matrices, and a general-purpose Minecraft client.

## Support Tiers

### Current Stable — blocking

The latest Mojang stable release from `version_manifest_v2.json` is the primary compatibility target. Patch, JAR integrity, and configured boot failures make the compatibility run fail.

### Current Development — advisory

The latest Mojang snapshot, release candidate, or pre-release is an early-warning target. Its result is visible in reports and workflow diagnostics, but failure does **not** make the compatibility command exit nonzero by itself and does not block a release known to work with stable Minecraft.

### Maintained Regression Fixtures — blocking when requested

Representative older versions remain available for manual/release regression checks when VanillaCord itself changes:

- `1.21.11`
- `1.20.6`
- `1.20.4`
- `1.19.4`
- `1.18.2`

When these are requested through `VANILLACORD_REQUIRED_SUPPORTED`, failures are blocking.

### Best-Effort Legacy — advisory

Historical targets are diagnostic unless intentionally promoted:

- `1.17.1`
- `1.16.5`
- `1.12.2`
- `1.8.9`
- `1.7.10`

Their failures are reported but do not make the command fail.

## Execution Model

### Scheduled sentinel

`.github/workflows/compatibility.yml` runs daily and remains stateless. It tests current stable plus current snapshot/RC without maintaining a database of previously seen versions.

The latest stable target receives the ephemeral boot smoke test. Snapshots are patch/integrity early-warning targets and are not booted. The executable tier policy is:

| Tier | Routine scheduled behavior | Exit-code effect |
| --- | --- | --- |
| `current-stable` | patch + integrity + boot | blocking |
| `current-development` | patch + integrity | advisory |
| `required-supported` | only when explicitly requested | blocking |
| `best-effort` | only when explicitly requested | advisory |

A current-development failure therefore produces a warning/report entry while preserving a zero exit status if every blocking target passed.

### Pull request validation

Changes to the compatibility workflow or probe trigger a narrowly scoped PR run that tests latest stable with patch, JAR integrity, and boot. Snapshot and historical coverage are disabled for this path to prove harness changes cheaply before merge.

### Manual regression matrix

`workflow_dispatch` retains maintained and best-effort matrices. Maintainers can override version sets, development inclusion, and stable boot smoke without changing repository state.

### Reports

Reports are emitted to the GitHub Actions job summary and retained as workflow artifacts. Each row states its tier and whether that tier is `blocking` or `advisory`; this makes the policy directly consumable by humans and automation rather than requiring inference from workflow status.

## Validation Ladder

1. **Patch** — VanillaCord exits successfully for the target Minecraft version.
2. **Integrity** — the expected patched output exists and is a readable JAR.
3. **Boot** — stable patched server reaches a known-good startup boundary in an ephemeral working directory and terminates cleanly.
4. **Forwarding boundary** — deterministic tests validate Velocity HMAC and forwarding wire data using the same parser production login handling consumes.
5. **Live proxy smoke, only if justified** — add a real Velocity/client fixture only if production failures demonstrate a material gap in the deterministic boundary.

## SourceScanner Hardening

Monitoring is evidence; stronger discovery prevents failures. Login discovery distinguishes strong hello-specific diagnostics from the broader `unexpected login` fallback, excludes acknowledgement text, and prevents later weak matches from replacing stronger evidence. Further structural signals should be added only in response to observed ambiguity.

## CI Policy

- Push/PR changes: normal unit/build validation.
- Compatibility-harness PR changes: latest stable patch + integrity + boot.
- Daily schedule: latest stable patch + integrity + boot, plus latest snapshot/RC patch + integrity as advisory evidence.
- Normal Java tests include deterministic Velocity forwarding-boundary and SourceScanner ambiguity/precedence coverage.
- Manual/release regression: current targets plus representative maintained versions as appropriate.
- Full legacy sweep: manual diagnostic operation, not routine release work.
- Stable and explicitly required-supported failures are blocking.
- Current-development and best-effort failures are advisory and do not independently produce a failing exit code.

## Current Implementation

Implemented:

- `scripts/check-minecraft-compatibility.sh` resolves Mojang current versions and runs repeatable probes.
- The script has explicit blocking and advisory failure accumulators rather than combining current snapshot into a generic required list.
- Reports contain `Tier` and `Policy` columns, making gating semantics machine-visible.
- A probe only passes patch/integrity when it creates a fresh, non-empty, readable `out/<version>.jar`.
- Latest stable can be boot-smoked in an isolated temporary server directory.
- `VelocityForwardingParser` isolates Velocity HMAC/wire parsing from Bridge and authlib runtime linkage; unit tests cover correct/wrong/rotated secrets and forwarded identity fields.
- `SourceScanner` preserves the older fallback while preferring stronger hello-specific evidence and rejecting acknowledgement diagnostics.
- `.github/workflows/compatibility.yml` supports a daily stateless sentinel, focused PR validation, and manual matrices with read-only repository/package permissions.
- Scheduled runs are bounded by timeout/concurrency and retain their report artifact.

## Stop Conditions

Do not add a live Velocity/client fixture if the deterministic boundary catches forwarding regressions at materially lower maintenance cost. If boot smoke becomes a source of frequent false failures, reduce it rather than adding orchestration. Do not add compatibility-management infrastructure unless repeated real failures show the simpler workflow is insufficient.

The success criterion is early, deterministic, actionable evidence of a Minecraft compatibility break with minimal maintenance burden.
