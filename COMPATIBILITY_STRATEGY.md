# Minecraft Compatibility Strategy

Last reviewed: 2026-08-28

## Purpose

VanillaCord is a bytecode patcher that discovers obfuscated Minecraft server
classes at patch time. Compatibility assurance should therefore answer one
question with the least machinery necessary:

> Does the current VanillaCord build still patch and operate against the
> Minecraft versions that matter?

The strategy deliberately favors deterministic, stateless checks over a
compatibility-management service. The monitor observes and reports; it does not
modify VanillaCord code automatically.

## Current Architecture

- `Downloader` reads Mojang's `version_manifest_v2.json`, downloads a requested
  server jar, verifies Mojang's SHA-1 metadata, and patches it.
- `Patcher` distinguishes modern bundled server jars from older fat jars by
  checking `Bundler-Format` in `META-INF/MANIFEST.MF`.
- `SourceScanner` discovers patch targets using string and structural signals.
- Login extension support contains version-era handling for older mutable packet
  classes, constructor-based packets, and modern record/interface packet shapes.
- Current Minecraft compatibility probes run with JDK 25; VanillaCord currently
  emits Java 21 bytecode for its own classes.

## Evidence From Prior Failures

The compatibility system must test more than a successful patcher exit code.

During the 2026-06 production fix, VanillaCord `v2.3` could read Java 25-era
classes but failed while patching current 26.x login flow. A partially written
bundled jar was cached and later failed at boot because a Minecraft class was
missing. The scanner also selected `handleLoginAcknowledgement` because
`Unexpected login acknowledgement packet` matched the loose `unexpected login`
heuristic. The subsequent fix excluded acknowledgement text and adapted to the
current offline-profile shape.

These incidents demonstrate two distinct risks:

1. patch output can be structurally invalid even when significant patch work has
   completed; and
2. heuristic source discovery can select the wrong target while still looking
   superficially plausible.

## Red-Team Decision

The project should build a **compatibility sentinel**, not a compatibility
platform.

High-value automation:

- periodically resolve Mojang's latest stable and snapshot/RC;
- build VanillaCord and patch those current versions;
- preserve a human-readable compatibility report and workflow diagnostics;
- keep current stable blocking and development snapshots as early warning;
- retain a manually triggered maintained/legacy matrix for regressions;
- add patch-output integrity, boot, and forwarding-boundary checks incrementally.

Explicit non-goals unless future evidence justifies them:

- autonomous code repair;
- per-version adapter tables or named mappings solely for monitoring;
- a compatibility database or persistent scheduler state;
- committing a new report file for every Mojang snapshot;
- automatically opening and closing issues for every transient probe failure;
- running the entire historical matrix every day;
- implementing a general-purpose Minecraft test client when a narrower
  forwarding-boundary probe is sufficient.

## Support Tiers

### Tier A: Current Stable

The latest Mojang stable release from `version_manifest_v2.json` is the primary
compatibility target. A failure is release-blocking once the probe includes the
required behavioral checks.

### Tier B: Current Development

The latest Mojang snapshot, release candidate, or pre-release is an early-warning
target. Failure should be visible but should not by itself prevent releasing a
VanillaCord build known to work with stable Minecraft.

### Tier C: Maintained Regression Fixtures

Representative older versions remain available for manual/release regression
checks when VanillaCord itself changes:

- `1.21.11`
- `1.20.6`
- `1.20.4`
- `1.19.4`
- `1.18.2`

### Best-Effort Legacy

These historical targets are diagnostic only unless intentionally promoted:

- `1.17.1`
- `1.16.5`
- `1.12.2`
- `1.8.9`
- `1.7.10`

## Execution Model

### Scheduled sentinel

`.github/workflows/compatibility.yml` runs daily. It is intentionally stateless:
it tests current stable plus current snapshot/RC on every scheduled execution
rather than maintaining a database of previously seen Mojang versions.

This spends a small amount of public-runner compute to avoid persistent state,
write permissions, synchronization logic, and repository churn. Concurrency is
bounded so a newer run cancels a redundant in-progress run.

The latest stable target additionally receives an ephemeral boot smoke test. The
server runs only on loopback, uses a disposable working directory and world, has
bounded heap, and must reach Minecraft's normal startup-complete marker before it
is stopped. Snapshots are not booted because their purpose is early warning and
because expanding behavioral coverage there would increase harness churn.

### Pull request validation

Runtime-affecting Java changes, `pom.xml`, and changes to the compatibility
workflow/probe trigger a narrowly scoped PR compatibility run. That review run
tests only the latest stable target with patch, jar integrity, and boot smoke
enabled. Snapshot and historical coverage are disabled so runtime changes are
proven before merge without duplicating the full regression matrix.

### Manual regression matrix

`workflow_dispatch` retains the maintained and best-effort matrices. Maintainers
can override the version sets, snapshot inclusion, and stable boot smoke without
changing repository state.

### Reports

Compatibility reports are emitted to the GitHub Actions job summary and retained
as workflow artifacts. The scheduled sentinel has read-only repository/package
permissions and does not commit generated reports back to `master`.

## Validation Ladder

Compatibility confidence is layered, stopping when another layer would cost more
to maintain than the failures it prevents:

1. **Patch** — VanillaCord exits successfully for the target Minecraft version.
2. **Integrity** — the expected patched output exists and is a readable jar.
3. **Boot** — the patched latest-stable server reaches a known-good startup
   boundary in an ephemeral working directory and is terminated cleanly.
4. **Forwarding boundary** — unit tests construct the actual Velocity forwarding
   wire payload, verify HMAC-SHA256 using configured/rotation secrets, decode the
   forwarded address, UUID, username, and profile-property tuples, and prove a
   wrong secret is rejected.

The fourth layer intentionally stops before launching a Velocity proxy or
Minecraft client. Production `VelocityHelper` consumes the same parsed value
object tested at the wire boundary. A live proxy/client fixture is justified only
if a real compatibility failure escapes these tests and demonstrates that the
additional machinery would provide materially better signal.

## SourceScanner Hardening

Monitoring is evidence; stronger discovery prevents failures. Engineering effort
should therefore favor SourceScanner robustness over elaborate CI reporting.

The first hardening increment ranks login signals while preserving backward
compatibility. Hello-specific diagnostics are strong signals; broad `unexpected
login` text is a weak fallback. A strong signal can replace a weak candidate
regardless of visitation order, while a later weak signal cannot overwrite a
strong candidate. Equal-strength matches in different methods are treated as
explicit ambiguity rather than silently selecting the last method. Multiple
matching signals in one method are allowed as corroboration. The historical
login-acknowledgement false positive is pinned as a regression test.

Startup and handshake hook discovery also reject multiple distinct matching
methods rather than using last-match-wins behavior.

Further scanner work should be driven by observed compatibility failures. Where
needed, combine constants with method/field shape or invocation context and emit
explicit discovery diagnostics. Do not introduce a generalized confidence model
without evidence that these simpler invariants are insufficient.

## CI Policy

- Push/PR changes: normal unit/build validation.
- Runtime-affecting Java/POM or compatibility-harness PR changes: latest stable
  patch + integrity + boot.
- Daily schedule: latest stable patch + integrity + boot, plus latest snapshot/RC
  patch + integrity.
- Manual/release regression: current targets plus representative maintained
  versions as appropriate.
- Full legacy sweep: manual diagnostic operation, not routine release work.
- Stable compatibility failures are blocking once the relevant behavioral checks
  are in place.
- Snapshot failures are early-warning evidence, not automatic proof of a
  VanillaCord defect.

## Current Implementation

Implemented:

- `scripts/check-minecraft-compatibility.sh` resolves Mojang current versions and
  runs repeatable patch probes.
- A probe only passes patch/integrity when the requested run creates a fresh,
  non-empty, readable `out/<version>.jar`.
- The latest stable target is boot-smoked in an isolated temporary server
  directory; success requires reaching the normal server startup marker before a
  graceful `stop` is sent.
- `VelocityForwardingParser` isolates the signed Velocity wire boundary from the
  Minecraft/Bridge callback and is directly covered for valid decoding, invalid
  secret rejection, and secret rotation. Authlib object construction remains at
  the production helper boundary rather than contaminating the wire test.
- `scripts/Invoke-CompatibilityProbe.ps1` provides a local Windows entry point.
- `.github/workflows/compatibility.yml` supports manual matrix runs, a daily
  stateless compatibility sentinel, and focused current-stable PR validation.
- Scheduled runs are restricted to current stable + current snapshot/RC, use a
  30-minute job timeout, cancel redundant in-progress runs, publish the report in
  the job summary, and retain the report artifact for 30 days.
- Normal build CI validates relevant pull requests before merge; its placeholder
  version guard uses runner-portable `grep` rather than assuming ripgrep exists.
- ASM `9.10.1` supports reading current Java 25-era class files.

Next implementation increments, in priority order:

1. prove the SourceScanner signal-ranking/ambiguity invariant against unit tests
   and the real current-stable patch + boot probe;
2. let the daily sentinel accumulate operational evidence across Mojang releases
   and fix only failure modes that actually appear;
3. consider release gating on the proven stable compatibility job once its signal
   has demonstrated low false-positive rates;
4. add a live Velocity/client fixture only if a real failure escapes the existing
   forwarding-boundary tests.

## Stop Conditions

Keep the forwarding assurance at the direct cryptographic/wire boundary unless a
real failure demonstrates that a live proxy fixture would have caught something
material. If a future live fixture requires materially more maintenance than
VanillaCord itself, produces mostly harness failures, or tracks Minecraft protocol
changes unrelated to forwarding, remove it.

If the boot fixture becomes a source of frequent false failures, reduce it to a
cheaper executable-jar/runtime sanity check rather than adding more server
orchestration. Do not add compatibility-management infrastructure unless repeated
real failures show that the simpler workflow is insufficient.

The success criterion is not maximum automation. It is early, deterministic,
actionable evidence of a Minecraft compatibility break with minimal maintenance
burden.
