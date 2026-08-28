# Instructions for AI Agents

If you are an automated agent working on this repository, preserve the fork's explicit artifact identity, compatibility contracts, and upstream-flowability.

## Tech stack
* **Java:** JDK 25 for current Minecraft compatibility probes; project bytecode remains Java 21 via `maven.compiler.release`.
* **Build tool:** Apache Maven 3.9.16 pinned by Apache Maven Wrapper 3.3.4. Use `./mvnw` or `mvnw.cmd`, never an unpinned system Maven for repository validation.

## Artifact identity
New artifacts from this repository are SupraCraft artifacts:

- VanillaCord: `io.github.supracraft.vanillacord:vanillacord`
- Bridge dependencies/plugins: `io.github.supracraft.bridge:*`
- canonical standalone JAR: `supracraft-vanillacord-<version>.jar`

`net.ME1312*` Maven coordinates are historical/upstream identity and must not be reintroduced into active POMs. Do not rename the neutral `vanillacord.*` Java packages merely for branding; preserving those packages reduces runtime/API churn and keeps changes practical to contribute upstream.

`VanillaCord.jar` is a temporary byte-identical compatibility alias. New automation must target the canonical versioned JAR or Maven coordinate.

## Version semantics
The checked-in development line uses `X.Y.Z-dev`; CI uses immutable `X.Y.Z-dev.<run>` versions. Release candidates use `X.Y.Z-rc.N`; stable releases use `X.Y.Z`.

Do not introduce `SNAPSHOT.<run>` forms. They are ordinary Maven versions with misleading snapshot terminology, not Maven snapshots.

Source/upstream provenance is separate from the version string. Preserve manifest/build metadata for the source repository, upstream repository, Git commit/ref/run, and exact Bridge coordinate.

## Authentication
This project reads canonical Bridge artifacts from the `SupraCraft/Bridge` GitHub Packages repository. Builds need a token with `read:packages` scope:

```sh
export GITHUB_TOKEN=your-personal-access-token
export GITHUB_ACTOR=your-github-username
```

## Compiling and verifying
The source POM pins a known exact Bridge baseline. For normal integration work, the resolver selects the newest canonical immutable Bridge development build:

```sh
export BRIDGE_VERSION=$(./scripts/resolve-bridge-version.sh)
./mvnw -B verify -Dbridge.version="$BRIDGE_VERSION"
```

For reproducibility or release investigation, use the exact recorded Bridge version instead of resolving again.

Quick checks:

```sh
./mvnw -B clean compile
./mvnw -B test
```

On Windows, use equivalent `mvnw.cmd` commands.

## Build and compatibility discipline
* Do not bypass the Maven Wrapper or alter its pinned Maven version without updating modernization documentation and CI evidence.
* Do not edit generated artifacts directly.
* Packaging/toolchain changes must preserve `scripts/verify-artifact-contract.sh` and the current-stable Minecraft patch/integrity/boot gate.
* Keep Bridge and VanillaCord independently versioned and record the exact canonical Bridge coordinate consumed by every VanillaCord artifact.
* The canonical and temporary alias JARs must remain byte-identical while the alias exists.
* Preserve `Source-Repository: SupraCraft/VanillaCord` and `Upstream-Repository: ME1312/VanillaCord` as distinct provenance facts.
* Check for more-specific nested `AGENTS.md` files if they are introduced later.
