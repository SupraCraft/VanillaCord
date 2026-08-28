# VanillaCord build modernization record

Last reviewed: 2026-08-28

## Status

The Maven 3 build modernization described by the original version of this document is **complete**. This file is retained as a design/history record, not as a queue of work for humans or agents.

The authoritative execution ledger is `docs/build-modernization-status.md`. Current operational rules are in `README.md`, `AGENTS.md`, `VERSIONING.md`, `ARTIFACT_IDENTITY.md`, `COMPATIBILITY_STRATEGY.md`, and `PROJECT_CONTRACT.json`.

Do not re-run the historical phases below merely because they appear in this document.

## Current proven baseline

As of 2026-08-28:

- source development line: `2.9.0-dev`
- canonical Maven identity: `io.github.supracraft.vanillacord:vanillacord`
- canonical standalone JAR: `supracraft-vanillacord-<version>.jar`
- historical `VanillaCord.jar` alias: retired and prohibited from current output
- Maven Wrapper: `3.3.4`
- Maven: `3.9.16`
- emitted bytecode: Java 21
- current-Minecraft compatibility lane: JDK 25
- Assembly: `3.8.0`
- Compiler: `3.15.0`
- Surefire: `3.5.6`
- Enforcer: `3.6.3`
- Versions Maven Plugin: `2.21.0`
- CycloneDX Maven Plugin: `2.9.3`
- JUnit Jupiter: `6.1.3`
- Fastjson2: `2.0.64`
- ASM: `9.10.1`
- Minecraft-facing authlib fixture: `9.0.75` for the Minecraft 26.2 baseline
- Minecraft-facing Netty fixture: split `netty-buffer`, `netty-common`, and `netty-transport` modules on `4.2.15.Final` for the Minecraft 26.2 baseline
- deterministic archive timestamp configured
- canonical JAR byte-for-byte reproducibility proven
- artifact contract/inventory, SBOM, metadata, reproducibility record, and SHA-256 checksums retained
- current stable Minecraft patch + integrity + boot is blocking
- current development Minecraft is advisory

Minecraft-facing fixture versions are dated compatibility facts, not universal “latest dependency” declarations. Future changes must derive them from the then-current stable Mojang runtime and prove compatibility.

## Completed modernization sequence

The project completed these phases through reviewed PRs; exact merge/evidence references are in `docs/build-modernization-status.md`:

1. artifact-contract baseline
2. Maven Wrapper 3.3.4 / Maven 3.9.16 and Enforcer
3. Assembly 3.8.0 packaging modernization
4. Compiler/Surefire/Versions plugin modernization
5. removal of unnecessary Antrun machinery
6. SupraCraft-owned artifact/Maven identity
7. retirement of the legacy unversioned JAR alias
8. reproducible canonical JAR proof
9. explicit blocking/advisory compatibility semantics
10. focused bundled/test dependency freshness
11. Minecraft-derived authlib/Netty compatibility-fixture alignment
12. Bridge build modernization and exact tested-artifact publication

## Decisions that remain in force

### Keep Assembly unless evidence justifies Shade

Do not migrate to Maven Shade Plugin merely because it exists. Consider Shade only if a real packaging requirement appears, such as resource/service transformers, relocation, or an Assembly limitation that cannot be expressed cleanly. Any experiment must compare artifact inventory, manifest/provenance, transformed classes, current-stable patch/boot, and forwarding tests.

### Keep Maven 4 off the required path until GA and proven

When Maven 4 reaches GA:

1. add a nonblocking compatibility lane;
2. validate the Bridge Maven plugin specifically;
3. run the same artifact/reproducibility/compatibility contracts;
4. observe normal changes/releases;
5. only then consider changing the wrapper/default.

Bridge should prove its Maven 4 compatibility before VanillaCord makes Maven 4 required.

### Treat Minecraft-facing dependencies as fixtures

Do not auto-update authlib or Netty from repository-latest data. They model the Minecraft runtime surface. Derive changes from stable Mojang metadata, isolate the change, and require current-stable compatibility evidence.

### Prefer narrow deterministic gates

Do not add broad Maven/JDK matrices, persistent compatibility databases, autonomous repair, or live proxy/client orchestration without observed failures that demonstrate the simpler sentinel is insufficient.

## Event-driven future work

The completed modernization leaves only evidence-driven follow-up:

- Maven 4 nonblocking compatibility after GA;
- Shade only after a demonstrated Assembly limitation;
- Minecraft-facing fixture updates when Mojang changes stable runtime expectations;
- stronger integration coverage only when deterministic tests miss a real failure;
- dependency/tool updates as small isolated changes when useful.

## Historical success criteria

The original modernization succeeded because the repository now has pinned supported tooling, fewer bespoke build mechanisms, explicit SupraCraft artifact identity, immutable development versions, exact provenance, deterministic/reproducible JARs, current compatibility gates, and a smaller number of maintenance judgment calls.

If a future agent sees older issue/PR text that conflicts with this current-state record, the merged repository state and current executable contracts take precedence.
