# Instructions for automated agents

This file defines the operational rules for automated agents working in `SupraCraft/VanillaCord`. Human-facing context lives in `README.md`; detailed policy lives in `VERSIONING.md`, `ARTIFACT_IDENTITY.md`, and `COMPATIBILITY_STRATEGY.md`. `PROJECT_CONTRACT.json` is the compact machine-readable summary.

## Repository role

VanillaCord patches vanilla Minecraft server JARs so they can be used behind BungeeCord, BungeeGuard, or Velocity forwarding. It is not intended for Paper servers, which have native proxy-forwarding support.

This repository is the SupraCraft-maintained fork of `ME1312/VanillaCord`. Preserve upstream attribution, but never publish new SupraCraft artifacts under upstream Maven identity.

## Non-negotiable artifact identity

- Maven coordinate: `io.github.supracraft.vanillacord:vanillacord:<version>`
- canonical standalone JAR: `supracraft-vanillacord-<version>.jar`
- Java packages remain `vanillacord.*`
- Bridge coordinates use `io.github.supracraft.bridge:*`
- `VanillaCord.jar` is historical only and MUST NOT be recreated by current builds, releases, tests, or automation
- `net.ME1312*` coordinates are historical/upstream identity and MUST NOT be reintroduced into active POMs

## Version semantics

- checked-in source line: `X.Y.Z-dev`
- ordinary CI: immutable `X.Y.Z-dev.<github-run-number>`
- release candidate: `X.Y.Z-rc.N`
- stable release/tag: `X.Y.Z` / `vX.Y.Z`
- do not introduce `SNAPSHOT` or `SNAPSHOT.<run>` naming
- Git SHA/ref/run belong in provenance, not in the version string
- Bridge and VanillaCord are independently versioned; record the exact Bridge coordinate consumed

## Toolchain

- use the repository Maven Wrapper only: `./mvnw` or `mvnw.cmd`
- wrapper version: 3.3.4
- Maven version: 3.9.16
- build/patcher bytecode: Java 21 (`maven.compiler.release=21`)
- classes under `vanillacord.server` that are injected into patched Minecraft servers: Java 8 (`server.runtime.compiler.release=8`), because the declared stable support matrix includes Java 8 server generations
- Bridge transformation runs after compilation and must preserve that injected-runtime bytecode ceiling
- generated `vanillacord.translation` runtime classes must remain Java 8 compatible
- current-Minecraft compatibility probes use JDK 25 unless the workflow changes deliberately
- do not make Maven 4 required until it is GA and has passed an explicit compatibility lane

## Authentication and Bridge

Bridge is resolved from `SupraCraft/Bridge` GitHub Packages. Local builds need package-read credentials, normally:

```sh
export GITHUB_TOKEN=your-personal-access-token
export GITHUB_ACTOR=your-github-username
```

The source POM pins an exact Bridge baseline. Integration work may resolve the newest immutable canonical development build:

```sh
export BRIDGE_VERSION="$(./scripts/resolve-bridge-version.sh)"
./mvnw -B verify -Dbridge.version="$BRIDGE_VERSION"
```

For releases and reproducibility investigations, use the exact recorded Bridge version rather than resolving again.

## Required validation contracts

For ordinary Java/build changes, preserve:

```sh
./mvnw -B verify
```

Packaging or toolchain changes must also preserve:

- `scripts/verify-artifact-contract.sh`
- byte-for-byte reproducibility proof in `scripts/verify-reproducible-build.sh`
- absence of historical `VanillaCord.jar`
- exact manifest/build provenance
- current-stable Minecraft patch + JAR-integrity + boot validation
- full stable-release supported-Minecraft matrix, including patched-runtime closure and classfile compatibility on each declared Java generation
- deterministic Velocity forwarding-boundary tests
- SourceScanner ambiguity/precedence tests

Compatibility policy is executable and must agree with `COMPATIBILITY_STRATEGY.md`:

- `current-stable`: blocking
- `required-supported`: blocking when explicitly requested
- `current-development`: advisory
- `best-effort`: advisory

Do not make development snapshots release-blocking without a deliberate policy change.

## Minecraft-facing dependencies

Treat `authlib` and Netty as Minecraft compatibility fixtures, not ordinary dependency-freshness targets. Their compile baselines should be derived from the current stable Mojang server metadata and changed in isolated PRs with current-stable compatibility evidence. Do not blindly update them to repository-latest versions.

Bundled dependencies such as Fastjson2/ASM and test-only dependencies may follow normal focused dependency-update practice, but do not bulk-upgrade unrelated dependencies.

## Change discipline

- work on a scoped branch and PR; do not bypass repository governance
- keep changes attributable to one failure domain when practical
- never edit generated outputs by hand when a generator is authoritative
- preserve `Source-Repository: SupraCraft/VanillaCord` and `Upstream-Repository: ME1312/VanillaCord` as distinct provenance facts
- prefer deterministic checks over agent judgment in CI
- avoid broad matrices, compatibility databases, autonomous repair, or live-proxy orchestration unless observed failures justify them
- check for more-specific nested `AGENTS.md` files if introduced later

## Documentation discipline

Do not copy volatile facts such as “latest Minecraft snapshot” or “latest CI build number” into static instructions unless explicitly labeled as a dated historical observation. Current compatibility status belongs in workflow output/artifacts. Historical design plans must be labeled historical and must not override current contracts.
