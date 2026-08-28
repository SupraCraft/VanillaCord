# VanillaCord
[![Build Status](https://github.com/SupraCraft/VanillaCord/actions/workflows/build.yml/badge.svg)](https://github.com/SupraCraft/VanillaCord/actions/workflows/build.yml)
[![Release Version](https://img.shields.io/github/release/SupraCraft/VanillaCord/all.svg)](https://github.com/SupraCraft/VanillaCord/releases)<br>

VanillaCord downloads and patches a vanilla Minecraft server so proxies can connect to it with your choice of
[BungeeCord](https://www.spigotmc.org/wiki/bungeecord-ip-forwarding/),
[BungeeGuard](https://www.spigotmc.org/resources/bungeeguard.79601/), or
[Velocity](https://docs.papermc.io/velocity/security#velocity-modern-forwarding) IP forwarding enabled.

```sh
java -jar supracraft-vanillacord-<version>.jar <minecraft-versions...>
```

## What VanillaCord does
VanillaCord is for vanilla Minecraft backend servers. It downloads the Mojang
server jar for each requested version, patches the jar, and writes the patched
server to `out/<version>.jar`. The patched server creates and reads a
`vanillacord.txt` file from its working directory.

Use VanillaCord when the backend server is vanilla. Do not install VanillaCord on
PaperMC. Paper has native Velocity forwarding support and should be configured
through Paper's own `config/paper-global.yml`.

## Fork and artifact identity
This repository is the SupraCraft-maintained fork of ME1312/VanillaCord. Original
upstream authorship and license history remain intact, but artifacts built and
published here identify SupraCraft as their producer.

Canonical Maven identity:

```text
io.github.supracraft.vanillacord:vanillacord:<version>
```

Canonical standalone filename:

```text
supracraft-vanillacord-<version>.jar
```

The historical `VanillaCord.jar` compatibility alias is not emitted by new
SupraCraft builds or releases. Historical releases may retain upstream-derived
filenames, but new consumers and automation should use the canonical versioned
filename or Maven coordinate. The Java packages remain `vanillacord.*` because
they are already neutral and keeping them stable reduces compatibility churn and
keeps source changes practical to contribute upstream.

See `ARTIFACT_IDENTITY.md` and `VERSIONING.md` for the machine-consumption and
version policy.

## Downloads
*For Minecraft* 1.7, 1.8, 1.9, 1.10, 1.11, 1.12, 1.13, 1.14, 1.15, 1.16, 1.17, 1.18, 1.19, 1.20, 1.21, snapshots, and pre-releases

<a href="https://github.com/SupraCraft/VanillaCord/releases">
<pre>https://github.com/SupraCraft/VanillaCord/releases</pre>
</a>

## Patching a vanilla server
Download the canonical release JAR, then run it with one or more Minecraft versions:

```sh
java -jar supracraft-vanillacord-2.9.0.jar 26.2
```

The patched server jar is written to:

```text
out/26.2.jar
```

Run the patched jar from the server directory that contains `server.properties`,
`eula.txt`, and `vanillacord.txt`:

```sh
java -Xms2G -Xmx2G -jar out/26.2.jar --nogui
```

Current Minecraft server releases require Java 25. Older Minecraft versions may
require older Java runtimes, so pin both the Minecraft version and runtime when
maintaining legacy servers.

## Velocity modern forwarding
For a vanilla backend behind Velocity, use one shared secret in three places:

- Velocity proxy: `forwarding.secret`
- VanillaCord backend: `vanillacord.txt`
- CapRover deployment: `FORWARDING_SECRET`, when using this workspace's Docker images

Set Velocity to modern forwarding in `velocity.toml`:

```toml
online-mode = true
player-info-forwarding-mode = "modern"
forwarding-secret-file = "forwarding.secret"
```

Put the same secret in `forwarding.secret`:

```text
replace-with-a-long-random-secret
```

On the patched vanilla backend, set `server.properties` so players cannot bypass
the proxy identity flow:

```properties
online-mode=false
enforce-secure-profile=false
network-compression-threshold=-1
```

Then configure `vanillacord.txt` in the backend server working directory:

```properties
version = 2.0
forwarding = velocity
seecret = replace-with-a-long-random-secret
```

The key is intentionally spelled `seecret` because that is the historical
VanillaCord configuration name. Repeat `seecret = ...` on additional lines only
when rotating secrets or temporarily accepting multiple proxy secrets.

Velocity modern forwarding only protects identity data. Still firewall or
otherwise restrict backend server ports so players cannot connect directly to a
backend server.

## PaperMC backends
PaperMC does not use VanillaCord. For Paper behind Velocity, use Paper's native
Velocity forwarding instead:

```yaml
proxies:
  velocity:
    enabled: true
    online-mode: true
    secret: "replace-with-a-long-random-secret"
```

Also keep the same backend `server.properties` posture used for proxy-only
servers:

```properties
online-mode=false
enforce-secure-profile=false
network-compression-threshold=-1
```

The Velocity `forwarding.secret` value, Paper `proxies.velocity.secret`, and any
CapRover `FORWARDING_SECRET` value must match exactly. If they do not, Velocity
login will fail with an invalid forwarding data or forwarding secret error.

## CapRover workspace behavior
In this workspace, the vanilla server image downloads a VanillaCord release and
patches the selected vanilla server version at runtime. Deployment code should
locate the canonical `supracraft-vanillacord-*.jar` release asset rather than
assuming an unversioned filename.

```text
MINECRAFT_SERVER_VERSION=26.2
FORWARDING_SECRET=replace-with-a-long-random-secret
SERVER_EULA=true
```

The Paper image does not use VanillaCord. It downloads Paper directly and should
use the same `FORWARDING_SECRET` as Velocity.

## Building
- The repository pins Apache Maven `3.9.16` with Apache Maven Wrapper `3.3.4`. Use `./mvnw` on Unix-like systems or `mvnw.cmd` on Windows; do not depend on a system Maven version.
- Use JDK 25 for current Minecraft compatibility checks. The Maven build emits Java 21 bytecode (`maven.compiler.release=21`).
- Canonical Bridge dependencies come from `io.github.supracraft.bridge` in the `SupraCraft/Bridge` GitHub Packages repository.
- The source POM pins a known exact Bridge baseline. Normal integration CI may resolve the newest immutable `X.Y.Z-dev.N` Bridge build and always records the exact coordinate consumed.
- `BRIDGE_OWNER` defaults to `SupraCraft`; `BRIDGE_VERSION` pins an exact canonical Bridge build.
- Example: `BRIDGE_OWNER=SupraCraft BRIDGE_VERSION=0.1.0-dev.34 ./mvnw -B verify`
- To exercise the newest canonical Bridge development build: `BRIDGE_VERSION=$(./scripts/resolve-bridge-version.sh) ./mvnw -B verify`
- Compatibility probe: `scripts/Invoke-CompatibilityProbe.ps1 -UseDocker` tests current Mojang release, optional snapshot/RC, required supported releases, and best-effort legacy releases.

Development versions are immutable `X.Y.Z-dev.<run>` coordinates, release candidates
are `X.Y.Z-rc.N`, and stable releases are `X.Y.Z`. The project does not use Maven
`SNAPSHOT` semantics for CI artifacts.

## GitHub Packages auth (local)
- You need a PAT with `read:packages` for the owner hosting Bridge (and `write:packages` if publishing Bridge).
- Keep auth in-repo to avoid host config issues: `export GH_CONFIG_DIR=$PWD/.gh && printf "%s\n" "$PAT" | gh auth login --with-token`
- Set `GITHUB_TOKEN=$PAT` so Maven and `scripts/resolve-bridge-version.sh` can read from `https://maven.pkg.github.com/${BRIDGE_OWNER}/Bridge`.

## GitHub Packages auth (CI)
The workflow uses `BRIDGE_PACKAGES_TOKEN` and `BRIDGE_PACKAGES_USERNAME` when
provided; otherwise it falls back to the repository `GITHUB_TOKEN` and actor.

## Current fork status
- Latest historical stable release: [`v2.8`](https://github.com/SupraCraft/VanillaCord/releases/tag/v2.8).
- Next normalized SupraCraft release line: `2.9.0`; development builds use `2.9.0-dev.<run>`.
- Current compatibility sentinel validates the current stable Minecraft release with patch, JAR-integrity, and boot checks.
- [Compatibility report](docs/minecraft-compatibility-report.md).
- Recent work includes Minecraft 26.2 authlib/GameProfile compatibility fixes and deterministic Velocity-forwarding validation.
