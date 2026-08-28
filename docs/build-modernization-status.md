# Build modernization execution status

Last updated: 2026-08-28

This file is the execution ledger for `MODERNIZATION_PLAN.md`. The plan defines policy and sequencing; this file records what actually changed and the evidence required before each tranche was merged.

## Baseline

Initial modernization baseline: `master` at `3008a186ed8535348403841dc829dee65eabe830`.

Runtime invariants remain unchanged: Java 21 bytecode, generated provenance manifest, exact Bridge coordinate capture, CycloneDX SBOM, SHA-256 checksums, deterministic forwarding tests, and current-stable Minecraft patch/integrity/boot validation. Artifact identity and naming are explicitly SupraCraft-owned while upstream lineage remains separate metadata.

## Tranche A — Maven 3 packaging/tooling baseline

PR #18 merged as `a5f0af09b1034c5af11e22cdcd24e96d66788f38`.

Implemented and proven: artifact contract/inventory; Assembly `3.8.0`; Compiler `3.15.0`; Surefire `3.5.6`; Versions `2.21.0`; Enforcer `3.6.3`; Maven/Java baselines; UTF-8; Antrun removal; standard LICENSE resources; focused stable patch+boot gating.

## Tranche B — Maven Wrapper

PR #19 merged as `05018b4405de225c338710e001c99320e0c63071`.

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

Bridge PR #8 merged as `50a1d9690b437393d07e7cfca69f154d41657768`:

- `maven-jar-plugin` `3.4.2` → `3.5.1`
- `maven-javadoc-plugin` `3.11.3` → `3.12.0`
- Maven Plugin Tools `3.15.2` confirmed current and left unchanged
- reactor build/test/SBOM, coordinate/provenance verification, standalone staging, and checksums passed.

Bridge PR #9 merged as `d5066547e70830457f33ab22cdad67df094dcdf1`:

- provided ASM compile baseline aligned from `9.7` to `9.10.1` in `bridge` and `bridge-asm`
- ASM remains provided rather than bundled
- reactor build/test/SBOM and artifact/provenance gates passed unchanged.

Bridge PR #10 merged on 2026-08-28:

- fixed `project.build.outputTimestamp` at `2000-01-01T00:00:00Z`
- proves byte-identical rebuilds for the three published Bridge JARs
- records SHA-256 reproducibility evidence before publication.

Bridge PR #11 is the follow-on publication-hardening tranche. It removes the remaining rebuild seam by promoting the exact tested/version-set POMs and JARs into GitHub Packages and release/static-Maven outputs. PR validation exercises the same promotion helper against a disposable local Maven repository and requires byte-for-byte equality between tested and deployed JARs.

## Tranche D — reproducible canonical VanillaCord JAR

PR #22 merged as `165f188fccfe8cb6b531666749f9a155cba933d3`.

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

PR #23 merged as `738c5b44b2d5d89265db86a9bed0e718256b734f`.

The strategy and executable policy now agree:

- `current-stable`: blocking
- `required-supported`: blocking when requested
- `current-development`: advisory
- `best-effort`: advisory
- reports include explicit `Policy` and `Tier`
- advisory failures remain visible and warn but do not independently produce a failing exit status.

The focused PR stable patch/integrity/boot gate and ordinary build/reproducibility validation both remained green.

## Tranche E — dependency and compatibility-fixture freshness

### Bundled and test dependencies

VanillaCord PR #24 merged as `f02e67e0a0e0ef7416e7b76c5caad2a371d59448`:

- bundled `com.alibaba.fastjson2:fastjson2` `2.0.51` → `2.0.64`
- build/tests, byte-identical rebuild, artifact contract, and current-stable Minecraft patch/integrity/boot all passed
- this directly exercises the `Downloader` Mojang metadata parsing path that uses Fastjson2.

VanillaCord PR #25 merged as `faf3994aba09693909e3cacfd762b05236716880`:

- test-only JUnit Jupiter `5.10.2` → `6.1.3`
- forwarding and SourceScanner regression tests remained green
- reproducibility, artifact contract, and current-stable Minecraft compatibility remained green.

ASM `9.10.1` is current in VanillaCord and Bridge. Surefire `3.5.6`, Maven Plugin Tools `3.15.2`, Compiler `3.15.0`, Enforcer `3.6.3`, Assembly `3.8.0`, Versions `2.21.0`, and CycloneDX `2.9.3` remain current for the selected Maven 3 baseline as reviewed on 2026-08-28.

### Minecraft-facing provided dependencies

These are compatibility fixtures, not ordinary freshness dependencies. Their versions are derived from the current stable Minecraft runtime rather than from an unconstrained repository "latest" query.

VanillaCord PR #27 merged as `7c39378e8b0f9b4789dc3b3eee2b92a95f203c11`:

- aligned provided `com.mojang:authlib` from `6.0.53` to Minecraft 26.2's `9.0.75`
- the first validation exposed a real API seam: authlib 9 removed the historical `GameProfile.getProperties()` compile-time accessor
- VanillaCord no longer directly links to that obsolete accessor and resolves modern three-argument and historical two-argument/mutable-property `GameProfile` shapes at the runtime boundary
- a focused current-authlib construction test was added
- authlib remains `provided`; no Mojang authlib classes are bundled
- unit tests, reproducible artifact proof, and JDK 25 current-stable patch/integrity/boot passed before merge.

VanillaCord PR #28 merged as `69e3b1614fe361b624338fd2d1a0ccb06c390900`:

- replaced stale provided `io.netty:netty-all:4.1.107.Final`
- aligned to Minecraft 26.2's `4.2.15.Final` line
- declares only the direct provided modules VanillaCord actually compiles against: `netty-buffer`, `netty-common`, and `netty-transport`
- Netty remains provided; no Netty runtime is bundled into the SupraCraft JAR
- forwarding tests, reproducibility/artifact contract, and JDK 25 current-stable patch/integrity/boot passed before merge.

Future authlib/Netty changes should continue to follow the same rule: derive the fixture from the stable Minecraft metadata, isolate the change, and require current-stable runtime evidence. Do not auto-update these dependencies independently of Minecraft.

## Remaining modernization

- complete Bridge PR #11 and prove that package/release publication promotes the tested bytes rather than rebuilding them
- after Maven 4 reaches GA, add a nonblocking Maven 4 compatibility lane before considering any default migration
- keep Shade deferred unless Assembly demonstrates a concrete packaging limitation
- continue compatibility-fixture updates only when Mojang changes the stable runtime or a real compatibility failure provides evidence.

## Deferred

Maven 4 remains nonblocking until GA and until Bridge passes a Maven 4 compatibility lane. Shade remains an experiment only if Assembly demonstrates a concrete limitation.
