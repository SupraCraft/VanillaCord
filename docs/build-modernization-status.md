# Build modernization execution status

Last updated: 2026-08-28

This file is the execution ledger for `MODERNIZATION_PLAN.md`. The plan defines policy and sequencing; this file records what was actually changed and the evidence required before each tranche is merged.

## Baseline

Initial modernization baseline: `master` at `3008a186ed8535348403841dc829dee65eabe830`.

Runtime invariants remain unchanged: Java 21 bytecode, stable `VanillaCord.jar` release filename, generated provenance manifest, exact Bridge version capture, CycloneDX SBOM, SHA-256 checksums, deterministic forwarding tests, and current-stable Minecraft patch/integrity/boot validation.

## Tranche A — Maven 3 packaging/tooling baseline

Branch: `modernize/maven3-toolchain`
PR: #18
Status: **merged**
Merge commit: `a5f0af09b1034c5af11e22cdcd24e96d66788f38`

Implemented and proven:

- added `scripts/verify-artifact-contract.sh`
- retain a sorted JAR-entry inventory as CI evidence
- require expected VanillaCord classes and bundled fastjson2/ASM classes
- require `LICENSE`
- reject representative provided authlib/Netty classes from the fat JAR
- validate generated main class, effective project version, exact Bridge version, and source commit provenance
- Maven Assembly Plugin `2.2-beta-5` → `3.8.0`
- Maven Compiler Plugin `3.13.0` → `3.15.0`
- Maven Surefire Plugin `3.2.5` → `3.5.6`
- Versions Maven Plugin CI invocation `2.16.2` → `2.21.0`
- added Maven Enforcer Plugin `3.6.3`
- enforce Maven `[3.9.0,4.0.0)` and Java `21+`
- removed `maven-antrun-plugin`
- copy `LICENSE` through standard Maven resources
- made POM/build/artifact-contract changes run the focused latest-stable Minecraft patch+boot PR gate
- made source/reporting encoding explicitly UTF-8

Merge evidence:

- normal Maven build/test/SBOM succeeded
- artifact-contract script succeeded
- artifact inventory retained with CI evidence
- current stable Minecraft patch + JAR integrity + boot succeeded
- no runtime source change was needed for the packaging migration

## Tranche B — Maven Wrapper

Branch: `modernize/maven-wrapper`
PR: #19
Status: implementation/validation in progress

Implemented:

- generated official Apache Maven Wrapper `3.3.4` using the Apache wrapper plugin itself
- use `only-script` distribution; no wrapper JAR is committed
- pin Maven distribution to `3.9.16`
- preserve executable mode on Unix `mvnw`
- switch build, release, and compatibility Maven commands to the wrapper
- assert `Apache Maven 3.9.16` before executing Maven work in CI
- record Maven and wrapper versions in build metadata
- update `AGENTS.md` and README to make the wrapper canonical
- correct README repository/release links and stale fork-status wording
- keep Enforcer as a second line of defense

Required merge evidence:

- wrapper reports Maven 3.9.16 under JDK 21 build and JDK 25 compatibility lanes
- normal unit/build/SBOM and artifact contract pass
- focused current-stable Minecraft patch/integrity/boot passes
- no system-Maven invocation remains on required build/release/compatibility paths

Rollback point: Tranche A merge `a5f0af09b1034c5af11e22cdcd24e96d66788f38`.

## Tranche C — reproducible release builds

Status: pending Tranche B acceptance

Planned:

- derive deterministic archive timestamp from the source commit
- set `project.build.outputTimestamp`
- build twice from the same commit with the same exact Bridge coordinate
- compare SHA-256 of `VanillaCord.jar`
- retain diagnostic inventories when hashes differ
- only make reproducibility a release gate after the experiment is consistently reliable

## Tranche D — dependency freshness

Status: pending build-system stabilization

Dependency updates remain intentionally separate from Maven/packaging migration. Bundled implementation dependencies, provided Minecraft/runtime APIs, Bridge, and test-only dependencies will be reviewed as distinct risk classes.

## Bridge follow-through

After VanillaCord's Maven 3 baseline is stable, Bridge receives the matching maintainability treatment: Maven Wrapper 3.3.4 / Maven 3.9.16, explicit Maven plugin versions, UTF-8, Enforcer, and artifact/provenance checks. Bridge and VanillaCord remain independently versioned.

## Deferred

Maven 4 remains nonblocking until a GA release exists and Bridge has passed its own compatibility lane. Shade remains an experiment only if current Assembly demonstrates a concrete limitation.
