# Build modernization execution status

Last updated: 2026-08-28

This file is the execution ledger for `MODERNIZATION_PLAN.md`. The plan defines policy and sequencing; this file records what was actually changed and the evidence required before each tranche is merged.

## Baseline

Known-good baseline before implementation: `master` at `3008a186ed8535348403841dc829dee65eabe830`.

Runtime invariants remain unchanged: Java 21 bytecode, stable `VanillaCord.jar` release filename, generated provenance manifest, exact Bridge version capture, CycloneDX SBOM, SHA-256 checksums, deterministic forwarding tests, and current-stable Minecraft patch/integrity/boot validation.

## Tranche A — Maven 3 packaging/tooling baseline

Branch: `modernize/maven3-toolchain`
PR: #18
Status: validation in progress

Implemented:

- add `scripts/verify-artifact-contract.sh`
- retain a sorted JAR-entry inventory as CI evidence
- require expected VanillaCord classes and bundled fastjson2/ASM classes
- require `LICENSE`
- reject representative provided authlib/Netty classes from the fat JAR
- validate generated main class, effective project version, exact Bridge version, and source commit provenance
- Maven Assembly Plugin `2.2-beta-5` → `3.8.0`
- Maven Compiler Plugin `3.13.0` → `3.15.0`
- Maven Surefire Plugin `3.2.5` → `3.5.6`
- Versions Maven Plugin CI invocation `2.16.2` → `2.21.0`
- add Maven Enforcer Plugin `3.6.3`
- enforce Maven `[3.9.0,4.0.0)` and Java `21+`
- remove `maven-antrun-plugin`
- copy `LICENSE` through standard Maven resources
- make POM/build/artifact-contract changes run the focused latest-stable Minecraft patch+boot PR gate

Required merge evidence:

- normal Maven build/test/SBOM job succeeds
- artifact-contract script succeeds
- artifact inventory is retained with CI evidence
- current stable Minecraft patch + JAR integrity + boot succeeds
- no runtime source changes are required to accommodate the build migration

Rollback point: baseline commit above. The packaging/plugin changes are contained in the POM, workflows, and contract script.

## Tranche B — Maven Wrapper

Status: pending Tranche A acceptance

Planned:

- add Apache Maven Wrapper 3.3.4 files
- pin Maven distribution to 3.9.16
- use wrapper commands in build, compatibility, and release workflows
- update `AGENTS.md` and README build commands to `./mvnw`
- keep Enforcer as a second line of defense

Acceptance: wrapper reports Maven 3.9.16 and produces the same semantic artifact contract as Tranche A.

## Tranche C — reproducible release builds

Status: pending Tranche B

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

## Deferred

Maven 4 remains nonblocking until a GA release exists and Bridge has passed its own compatibility lane. Shade remains an experiment only if current Assembly demonstrates a concrete limitation.
