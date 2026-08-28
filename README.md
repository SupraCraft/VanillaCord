# VanillaCord

[![Build Status](https://github.com/SupraCraft/VanillaCord/actions/workflows/build.yml/badge.svg)](https://github.com/SupraCraft/VanillaCord/actions/workflows/build.yml)
[![Release Version](https://img.shields.io/github/release/SupraCraft/VanillaCord/all.svg)](https://github.com/SupraCraft/VanillaCord/releases)

VanillaCord downloads and patches a vanilla Minecraft server so proxies can connect using BungeeCord, BungeeGuard, or Velocity forwarding.

```sh
java -jar supracraft-vanillacord-<version>.jar <minecraft-versions...>
```

## Repository role

VanillaCord is for **vanilla Minecraft backend servers**. It downloads the Mojang server JAR for each requested version, patches it, and writes the patched server to `out/<version>.jar`.

Servers that already provide their own native proxy-forwarding implementation are outside this repository's scope; use that server's own documentation instead.

This repository is the SupraCraft-maintained fork of `ME1312/VanillaCord`. Upstream authorship/license history remain intact, but new artifacts identify SupraCraft as their producer.

## Documentation map

- `README.md` — human entry point and operating quickstart
- `AGENTS.md` — automated-agent rules
- `PROJECT_CONTRACT.json` — compact machine-readable repository contract
- `ARTIFACT_IDENTITY.md` — producer/upstream artifact identity
- `VERSIONING.md` — immutable version/provenance rules
- `COMPATIBILITY_STRATEGY.md` — compatibility policy/rationale
- `docs/compatibility.md` — executable compatibility operations
- `docs/build-modernization-status.md` — completed modernization evidence ledger
- `MODERNIZATION_PLAN.md` — historical modernization record, not an active work queue

## Artifact identity

Canonical Maven identity:

```text
io.github.supracraft.vanillacord:vanillacord:<version>
```

Canonical standalone filename:

```text
supracraft-vanillacord-<version>.jar
```

The historical `VanillaCord.jar` alias is retired. Current builds/releases must not emit it. Java packages remain `vanillacord.*` to preserve compatibility and upstream-flowability.

## Patching a vanilla server

Download an exact release JAR and run it with one or more Minecraft versions:

```sh
java -jar supracraft-vanillacord-2.9.0.jar 26.2
```

The patched server is written to:

```text
out/26.2.jar
```

Run the patched server from the directory containing `server.properties`, `eula.txt`, and `vanillacord.txt`:

```sh
java -Xms2G -Xmx2G -jar out/26.2.jar --nogui
```

Runtime Java requirements are determined by the selected Minecraft release. The current compatibility sentinel uses JDK 25 for current Minecraft while VanillaCord itself emits Java 21 bytecode.

## Velocity modern forwarding

Use one shared secret between Velocity and the VanillaCord backend.

Velocity `velocity.toml`:

```toml
online-mode = true
player-info-forwarding-mode = "modern"
forwarding-secret-file = "forwarding.secret"
```

`forwarding.secret`:

```text
replace-with-a-long-random-secret
```

Backend `server.properties` for a proxy-only vanilla backend:

```properties
online-mode=false
enforce-secure-profile=false
network-compression-threshold=-1
```

Backend `vanillacord.txt`:

```properties
version = 2.0
forwarding = velocity
seecret = replace-with-a-long-random-secret
```

`seecret` is intentionally spelled that way for historical VanillaCord configuration compatibility. Additional `seecret = ...` lines may be used during controlled secret rotation.

Velocity forwarding protects forwarded identity data; still firewall/restrict backend ports so clients cannot bypass the proxy.

## BungeeCord / BungeeGuard

VanillaCord also supports the historical BungeeCord and BungeeGuard forwarding paths. Preserve their existing configuration semantics when changing forwarding code, and add focused regression tests for protocol/handshake edge cases. `docs/bot-disconnection-fix.md` is a historical incident record for one BungeeGuard failure mode, not current deployment instructions.

## Building

The repository pins Maven `3.9.16` through Maven Wrapper `3.3.4`. Use the wrapper, not a system Maven:

```sh
./mvnw -B verify
```

Windows:

```powershell
.\mvnw.cmd -B verify
```

The source POM pins an exact Bridge baseline. Canonical Bridge artifacts come from `io.github.supracraft.bridge` in the `SupraCraft/Bridge` GitHub Packages repository.

For normal integration work, resolve the newest canonical immutable Bridge development build and record the exact result:

```sh
export BRIDGE_OWNER="${BRIDGE_OWNER:-SupraCraft}"
export BRIDGE_VERSION="$(./scripts/resolve-bridge-version.sh)"
./mvnw -B verify -Dbridge.version="$BRIDGE_VERSION"
```

For release or reproducibility work, supply the exact previously selected Bridge version rather than resolving again:

```sh
export BRIDGE_VERSION="<exact-bridge-version>"
./mvnw -B verify -Dbridge.version="$BRIDGE_VERSION"
```

GitHub Packages access normally requires a token with `read:packages` plus the matching GitHub actor/user identity.

## Version semantics

- source line: `X.Y.Z-dev` (currently `2.9.0-dev`)
- ordinary CI: immutable `X.Y.Z-dev.<github-run-number>`
- release candidate: `X.Y.Z-rc.N`
- stable release/tag: `X.Y.Z` / `vX.Y.Z`
- Maven `SNAPSHOT` semantics are intentionally not used

Bridge and VanillaCord version independently. Every VanillaCord artifact records the exact Bridge coordinate it consumed.

## Compatibility sentinel

The canonical implementation is:

```sh
scripts/check-minecraft-compatibility.sh
```

When no JAR argument is supplied it requires exactly one `artifacts/supracraft-vanillacord-*.jar` artifact.

Policy:

| Tier | Effect |
| --- | --- |
| current stable | blocking |
| explicitly required supported versions | blocking |
| current development snapshot/RC | advisory |
| best-effort legacy | advisory |

Current workflow evidence is authoritative; static checked-in tables are not treated as evergreen compatibility status. See `docs/compatibility.md` and `COMPATIBILITY_STRATEGY.md`.

## Build and release evidence

Current CI/release validation retains:

- generated manifest/source/upstream provenance
- exact Bridge coordinate
- CycloneDX SBOM
- artifact inventory
- `BUILD-METADATA.properties`
- `REPRODUCIBILITY.properties`
- SHA-256 checksums
- byte-for-byte canonical JAR reproducibility proof
- artifact contract checks that bundled/provided dependency boundaries remain correct
- current-stable Minecraft patch/integrity/boot evidence where required

## Current fork state

- historical upstream-derived releases/tags remain preserved
- normalized SupraCraft development line is `2.9.0-dev`
- canonical identity/naming migration is complete
- Maven 3 build modernization and reproducibility work are complete
- authlib/Netty compile fixtures are derived from stable Minecraft compatibility evidence rather than unconstrained dependency-latest queries
- future modernization is event-driven: Maven 4 only after GA/proven compatibility; Shade only after a demonstrated Assembly limitation; stronger integration tests only after observed gaps
