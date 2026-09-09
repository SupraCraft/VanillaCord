# Instructions for automated agents

This repository is the standalone public source, build, package, release, and documentation projection for SupraCraft VanillaCord.

## Authority boundary

- Normal product development and specialized validation remain authoritative in the private development plane.
- Public changes arrive through reviewed constructive projection; do not implement independent feature work here.
- Public CI runs only on this tree and uses its own `GITHUB_TOKEN` with `packages: read` for the public Bridge repository.
- Do not add private evaluators, hidden corpora, private-value material, private tokens, or private-repository dependencies.

## Project identity

VanillaCord patches vanilla Minecraft server JARs for proxy forwarding. Preserve attribution to `ME1312/VanillaCord`; new public-era SupraCraft artifacts use `io.github.supracraft:vanillacord:<version>` and the canonical `supracraft-vanillacord-<version>.jar`.

The historical `2.9.0` identity and `VanillaCord.jar` alias are retained only as historical evidence and must not be recreated by current builds.

## Build and release

- Use the pinned Maven Wrapper 3.3.4 / Maven 3.9.16 and Java 21 tooling baseline.
- Injected server-runtime classes remain Java 8 compatible.
- Public release workflows must build once, promote tested bytes, record exact Bridge coordinates, and publish only from this repository.
- Exact Bridge release qualification uses `io.github.supracraft:bridge:0.1.1-rc.1` (or the explicitly qualified immutable replacement).
