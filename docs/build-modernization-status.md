# Build modernization execution status

Last updated: 2026-08-28

This file is the execution ledger for `MODERNIZATION_PLAN.md`. The plan defines policy and sequencing; this file records what was actually changed and the evidence required before each tranche is merged.

## Baseline

Initial modernization baseline: `master` at `3008a186ed8535348403841dc829dee65eabe830`.

Runtime invariants remain unchanged: Java 21 bytecode, generated provenance manifest, exact Bridge coordinate capture, CycloneDX SBOM, SHA-256 checksums, deterministic forwarding tests, and current-stable Minecraft patch/integrity/boot validation. Artifact identity and naming are explicitly SupraCraft-owned while upstream lineage remains separate metadata.

## Tranche A — Maven 3 packaging/tooling baseline

PR: #18  
Status: **merged**  
Merge commit: `a5f0af09b1034c5af11e22cdcd24e96d66788f38`

Implemented and proven: artifact contract/inventory; Assembly `3.8.0`; Compiler `3.15.0`; Surefire `3.5.6`; Versions `2.21.0`; Enforcer `3.6.3`; Maven/Java baselines; UTF-8; Antrun removal; standard LICENSE resources; focused stable patch+boot gating.

## Tranche B — Maven Wrapper

PR: #19  
Status: **merged**  
Merge commit: `05018b4405de225c338710e001c99320e0c63071`

Implemented and proven: Apache Maven Wrapper `3.3.4`; Maven `3.9.16`; wrapper authoritative in build/release/compatibility paths; JDK 21/JDK 25 Maven assertions; wrapper provenance recorded.

## Tranche C — SupraCraft artifact identity and immutable development versions

Bridge PR #3 merged as `3accd1ad5548e0b16a58e0665b9c40953c6124ef` with canonical `io.github.supracraft.bridge` coordinates and immutable `0.1.0-dev.<run>` CI versions.

VanillaCord PR #20 merged as `303d2af90a3c7b6afbebe334ce62ddc1cf626d76` with:

- canonical `io.github.supracraft.vanillacord:vanillacord`
- source line `2.9.0-dev`
- CI `2.9.0-dev.<run>`, RC `2.9.0-rc.N`, stable `2.9.0`
- canonical Bridge coordinates
- standalone `supracraft-vanillacord-<version>.jar`
- separate SupraCraft source and ME1312 upstream provenance
- neutral `vanillacord.*` Java packages retained.

### Tranche C.1 — retire legacy standalone alias

PR #21 merged as `f6649e4c4a12c42d2e95f95963d60e0d6b7a2bee`.

- stopped creating/publishing `VanillaCord.jar`
- CI asserts the alias is absent
- compatibility harness discovers exactly one canonical SupraCraft JAR when no path is supplied
- JDK 21 artifact/provenance and JDK 25 current-stable patch/integrity/boot gates passed.

## Bridge build modernization and standalone naming

Bridge PR #6 merged as `ee3c7a89fdb9a2d822dbf332650d610b350eab10`:

- Maven Wrapper `3.3.4` / Maven `3.9.16`
- stable plugin modernization, UTF-8, Enforcer, Antrun removal
- wrapper authoritative; documentation-only pushes do not publish meaningless dev coordinates.

Bridge PR #7 merged as `bfbbe3f3e87114d6d1cb7623e6c0455951a233c1`:

- Maven repository layout remains conventional
- Actions/releases expose `supracraft-bridge-*`, `supracraft-bridge-asm-*`, and `supracraft-bridge-plugin-*`
- versioned SupraCraft SBOM, metadata, and checksums accompany standalone files.

## Tranche D — reproducible canonical JARs

PR: #22  
Status: **merged**  
Merge commit: `165f188fccfe8cb6b531666749f9a155cba933d3`

Implemented and proven:

- fixed `project.build.outputTimestamp` at `2000-01-01T00:00:00Z`
- normal validated build is reproducibility sample one; one clean rebuild is sample two
- both use the same effective version, exact Bridge coordinate, source provenance, build number, Maven Wrapper, JDK lane, and archive timestamp
- canonical JARs must be byte-identical and have identical SHA-256
- mismatch diagnostics retain entry lists and ZIP metadata
- `REPRODUCIBILITY.properties` records proven JAR hash and exact Bridge input
- release path performs the same proof before publication
- JDK 21 build/artifact contract passed after the clean rebuild
- JDK 25 current-stable Minecraft patch/integrity/boot remained green.

CycloneDX byte-for-byte reproducibility is intentionally out of scope; the executable JAR is the reproducibility target while SBOM semantic/dependency evidence remains retained.

## Tranche D.1 — align compatibility gating semantics

Branch: `modernize/snapshot-advisory-semantics`  
Status: **validation in progress**

Problem found during red-team cleanup: the strategy correctly described current Minecraft snapshots/RCs as advisory, but the script appended the snapshot to a generic required list, so a development failure could make the scheduled command exit nonzero.

Implemented:

- `current-stable`: blocking
- `required-supported`: blocking when requested
- `current-development`: advisory
- `best-effort`: advisory
- separate blocking/advisory failure accumulators
- report rows include explicit `Policy` as well as `Tier`
- advisory failures remain visible and warn on stderr but do not independently produce a failing exit code
- strategy documentation now describes the executable policy rather than relying on implied semantics.

Required merge evidence: focused PR stable patch/integrity/boot remains green and ordinary build/reproducibility validation remains green.

## Tranche E — dependency freshness

Status: pending sentinel cleanup

Bundled implementation dependencies, provided Minecraft/runtime APIs, Bridge, and test-only dependencies will be reviewed as separate risk classes rather than updated as one bulk operation.

## Deferred

Maven 4 remains nonblocking until GA and until Bridge passes a Maven 4 compatibility lane. Shade remains an experiment only if Assembly demonstrates a concrete limitation.
