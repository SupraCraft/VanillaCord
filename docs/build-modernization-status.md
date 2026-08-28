# Build modernization execution status

Last updated: 2026-08-28

This file is the execution ledger for `MODERNIZATION_PLAN.md`. The plan defines policy and sequencing; this file records what was actually changed and the evidence required before each tranche is merged.

## Baseline

Initial modernization baseline: `master` at `3008a186ed8535348403841dc829dee65eabe830`.

Runtime invariants remain unchanged: Java 21 bytecode, generated provenance manifest, exact Bridge coordinate capture, CycloneDX SBOM, SHA-256 checksums, deterministic forwarding tests, and current-stable Minecraft patch/integrity/boot validation. Artifact naming is intentionally changing during the identity tranche; a byte-identical `VanillaCord.jar` alias preserves temporary operational compatibility.

## Tranche A — Maven 3 packaging/tooling baseline

Branch: `modernize/maven3-toolchain`
PR: #18
Status: **merged**
Merge commit: `a5f0af09b1034c5af11e22cdcd24e96d66788f38`

Implemented and proven:

- artifact-contract script and sorted JAR inventory
- Assembly `3.8.0`, Compiler `3.15.0`, Surefire `3.5.6`, Versions `2.21.0`, Enforcer `3.6.3`
- Maven `[3.9.0,4.0.0)` and Java `21+` enforcement
- removed Antrun from VanillaCord
- standard Maven LICENSE resources
- explicit UTF-8
- focused latest-stable Minecraft patch+boot gate on build-system changes

Merge evidence: Maven build/test/SBOM, artifact contract, inventory, and current-stable patch/integrity/boot all succeeded without runtime source changes.

## Tranche B — Maven Wrapper

Branch: `modernize/maven-wrapper`
PR: #19
Status: **merged**
Merge commit: `05018b4405de225c338710e001c99320e0c63071`

Implemented and proven:

- official Apache Maven Wrapper `3.3.4`, generated with the Apache wrapper plugin
- Maven `3.9.16` pinned
- executable Unix wrapper and Windows wrapper script committed; no wrapper JAR
- build, release, and compatibility paths use `./mvnw`
- JDK 21 and JDK 25 CI both assert Maven `3.9.16`
- Maven/wrapper versions recorded in build metadata
- artifact contract and current-stable Minecraft patch/integrity/boot passed through the wrapper

## Tranche C — SupraCraft artifact identity and immutable development versions

Bridge producer prerequisite:

- `SupraCraft/Bridge` PR #3 merged as `3accd1ad5548e0b16a58e0665b9c40953c6124ef`
- canonical Bridge group: `io.github.supracraft.bridge`
- canonical Bridge source line: `0.1.0-dev`
- first canonical master publication: `0.1.0-dev.34`
- Bridge manifests distinguish `Source-Repository: SupraCraft/Bridge` from `Upstream-Repository: ME1312/Bridge`

VanillaCord branch: `modernize/artifact-identity`
VanillaCord PR: #20
Status: **validation in progress**

Implemented:

- canonical Maven coordinate `io.github.supracraft.vanillacord:vanillacord`
- checked-in source line `2.9.0-dev`
- CI form `2.9.0-dev.<run>`; no fake `SNAPSHOT.<run>` terminology
- RC form `2.9.0-rc.N`; stable form `2.9.0`
- canonical Bridge dependencies/plugin under `io.github.supracraft.bridge`
- source-pinned Bridge baseline `0.1.0-dev.34`
- development resolver selects only canonical immutable Bridge `X.Y.Z-dev.N` builds
- release builds use the source-pinned exact Bridge version unless explicitly overridden
- canonical JAR `supracraft-vanillacord-<version>.jar`
- temporary `VanillaCord.jar` compatibility alias created by copying the canonical artifact
- CI requires alias byte identity with `cmp`
- JAR manifest records SupraCraft producer, source repository, upstream repository, and exact Bridge coordinate
- build metadata records canonical Maven identity plus source/upstream lineage
- Java packages remain `vanillacord.*` to avoid unnecessary compatibility and upstream-flow churn

Required merge evidence:

- JDK 21 build/test/SBOM passes against a published canonical Bridge coordinate
- artifact contract validates canonical filename, producer/source/upstream provenance, and exact Bridge coordinate
- compatibility alias is byte-identical to the canonical JAR
- CycloneDX reports SupraCraft VanillaCord and Bridge coordinates
- JDK 25 focused current-stable Minecraft patch/integrity/boot succeeds using the canonical JAR

## Tranche D — reproducible release builds

Branch reserved: `modernize/reproducible-builds`
Status: pending artifact-identity acceptance

Planned:

- set a deterministic `project.build.outputTimestamp`
- build twice from the same source/version/exact Bridge coordinate
- compare canonical JAR SHA-256
- retain diagnostic inventories if hashes differ
- gate releases only after repeatability is proven

## Tranche E — dependency freshness

Status: pending build-system and identity stabilization

Bundled implementation dependencies, provided Minecraft/runtime APIs, Bridge, and test-only dependencies are reviewed as separate risk classes rather than updated as one bulk operation.

## Bridge follow-through

Bridge artifact identity is complete, but its build-tool modernization remains separate work: Maven Wrapper `3.3.4` / Maven `3.9.16`, explicit modern plugin versions, UTF-8, Enforcer, and removal of remaining legacy build machinery. Bridge and VanillaCord remain independently versioned.

## Deferred

Maven 4 remains nonblocking until GA and until Bridge passes a Maven 4 compatibility lane. Shade remains an experiment only if Assembly demonstrates a concrete limitation.
