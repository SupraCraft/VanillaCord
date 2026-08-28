# Build modernization execution status

Last updated: 2026-08-28

This file is the execution ledger for `MODERNIZATION_PLAN.md`. The plan defines policy and sequencing; this file records what was actually changed and the evidence required before each tranche is merged.

## Baseline

Initial modernization baseline: `master` at `3008a186ed8535348403841dc829dee65eabe830`.

Runtime invariants remain unchanged: Java 21 bytecode, generated provenance manifest, exact Bridge coordinate capture, CycloneDX SBOM, SHA-256 checksums, deterministic forwarding tests, and current-stable Minecraft patch/integrity/boot validation. Artifact identity and naming are now explicitly SupraCraft-owned while upstream lineage remains separate metadata.

## Tranche A — Maven 3 packaging/tooling baseline

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

## Tranche B — Maven Wrapper

PR: #19
Status: **merged**
Merge commit: `05018b4405de225c338710e001c99320e0c63071`

Implemented and proven:

- official Apache Maven Wrapper `3.3.4`
- Maven `3.9.16` pinned
- build, release, and compatibility paths use `./mvnw`
- JDK 21 and JDK 25 CI assert Maven `3.9.16`
- Maven/wrapper versions recorded in build metadata
- artifact contract and current-stable Minecraft patch/integrity/boot passed through the wrapper

## Tranche C — SupraCraft artifact identity and immutable development versions

Bridge producer prerequisite:

- Bridge PR #3 merged as `3accd1ad5548e0b16a58e0665b9c40953c6124ef`
- canonical Bridge group `io.github.supracraft.bridge`
- canonical Bridge source line `0.1.0-dev`
- immutable CI versions `0.1.0-dev.<run>`
- source/upstream provenance separated in manifests and build evidence

VanillaCord PR #20:
Status: **merged**
Merge commit: `303d2af90a3c7b6afbebe334ce62ddc1cf626d76`

Implemented and proven:

- canonical Maven coordinate `io.github.supracraft.vanillacord:vanillacord`
- checked-in source line `2.9.0-dev`
- immutable CI form `2.9.0-dev.<run>`; no fake `SNAPSHOT.<run>` terminology
- RC form `2.9.0-rc.N`; stable form `2.9.0`
- Bridge dependencies/plugin under `io.github.supracraft.bridge`
- source-pinned exact Bridge baseline and canonical dev resolver
- canonical standalone JAR `supracraft-vanillacord-<version>.jar`
- JAR manifest and build metadata distinguish SupraCraft source identity from ME1312 upstream lineage
- Java packages remain neutral `vanillacord.*`

## Tranche C.1 — retire legacy standalone alias

Branch: `modernize/retire-legacy-artifact-alias`
Status: **validation in progress**

Implemented:

- stop creating or publishing `VanillaCord.jar`
- require the legacy alias to be absent from build/release output
- checksum and upload only the canonical versioned SupraCraft JAR
- README and artifact-identity policy make the versioned filename exclusive for new builds
- historical releases remain unchanged as historical evidence

Required merge evidence:

- JDK 21 build/test/SBOM and artifact contract pass
- build artifact contains only the canonical standalone JAR plus evidence files
- JDK 25 current-stable Minecraft patch/integrity/boot passes using the canonical JAR

## Bridge build modernization and standalone naming

Bridge PR #6:
Status: **merged**
Merge commit: `ee3c7a89fdb9a2d822dbf332650d610b350eab10`

- Apache Maven Wrapper `3.3.4` / Maven `3.9.16`
- modern stable build plugins, UTF-8, Enforcer, and Antrun removal
- wrapper authoritative in CI/publish paths
- documentation-only pushes do not create meaningless new dev coordinates

Bridge PR #7:
Status: **merged**
Merge commit: `bfbbe3f3e87114d6d1cb7623e6c0455951a233c1`

- Maven repository layout stays conventional
- Actions/release downloads use explicit `supracraft-bridge-*`, `supracraft-bridge-asm-*`, and `supracraft-bridge-plugin-*` filenames
- versioned SupraCraft SBOM plus metadata/checksums accompany standalone files

## Tranche D — reproducible release builds

Status: next after alias retirement

Planned:

- set deterministic `project.build.outputTimestamp`
- build twice from the same source/version/exact Bridge coordinate
- compare canonical JAR SHA-256
- retain diagnostic inventories if hashes differ
- gate releases only after repeatability is proven

The reproducibility branch must be recreated from current master rather than relying on the earlier reserved branch, which predates the artifact-identity migration.

## Tranche E — dependency freshness

Status: pending reproducibility baseline

Bundled implementation dependencies, provided Minecraft/runtime APIs, Bridge, and test-only dependencies are reviewed as separate risk classes rather than updated as one bulk operation.

## Deferred

Maven 4 remains nonblocking until GA and until Bridge passes a Maven 4 compatibility lane. Shade remains an experiment only if Assembly demonstrates a concrete limitation.
