# VanillaCord versioning and provenance

VanillaCord and Bridge use independent versioning. VanillaCord never shares Bridge's version number; every build records the exact canonical Bridge coordinate it consumed.

## Canonical identity

New artifacts from this fork use:

```text
io.github.supracraft.vanillacord:vanillacord:<version>
```

The historical `net.ME1312:VanillaCord` coordinate identifies upstream/history and is not used for new SupraCraft artifacts. Java packages remain `vanillacord.*` because they are already neutral API/runtime names.

The canonical standalone JAR is:

```text
supracraft-vanillacord-<version>.jar
```

`VanillaCord.jar` is historical only. Current CI and releases MUST NOT emit it. Historical releases may retain old filenames as immutable historical evidence.

## Source and development versions

The checked-in POM is the source of truth for the next release line and carries `X.Y.Z-dev`. The current source line is `2.9.0-dev`.

Ordinary CI appends the GitHub Actions run number:

```text
X.Y.Z-dev.<run-number>
```

These are immutable ordinary Maven versions. `SNAPSHOT` is intentionally not used. Forms such as `2.9-SNAPSHOT.62` did not end in `-SNAPSHOT`, so Maven did not treat them as snapshots; the terminology was misleading and is retired.

## Release candidates and releases

Release candidates use `X.Y.Z-rc.N`. Stable releases use `X.Y.Z`; tags use `vX.Y.Z`. Historical tags remain historical and are not rewritten.

A release build derives its project version from the explicit release/tag input. After a stable release, the checked-in POM advances deliberately to the next intended `X.Y.Z-dev` line.

## Bridge relationship

Canonical Bridge coordinates use `io.github.supracraft.bridge`. Development integration CI may resolve the newest immutable `X.Y.Z-dev.N` Bridge build to expose integration failures early. Every resulting VanillaCord artifact records the exact coordinate consumed.

Release and reproducibility work must use an exact immutable Bridge version. Do not rely on mutable `latest` metadata as a release input.

## Embedded provenance

Every canonical JAR records:

- `Implementation-Title: VanillaCord`
- `Implementation-Version`
- `Implementation-Vendor: SupraCraft`
- `Build-Commit`
- `Build-Ref`
- `Build-Number`
- `Source-Repository: SupraCraft/VanillaCord`
- `Upstream-Repository: ME1312/VanillaCord`
- `Bridge-Version`
- `Bridge-Coordinate: io.github.supracraft.bridge:bridge:<exact-version>`

CI additionally emits build evidence including:

- CycloneDX JSON SBOM
- `BUILD-METADATA.properties`
- `ARTIFACT-INVENTORY.txt`
- `REPRODUCIBILITY.properties`
- `SHA256SUMS`

The checksum set covers the current canonical artifact/evidence set; it does not include the retired `VanillaCord.jar` alias.

## Reproducibility

Version strings identify release/development state, not source provenance. Git commit/ref/run, exact Bridge coordinate, wrapper/Maven inputs, SBOM, metadata, and checksums carry reconstruction evidence separately.

The build uses a fixed archive output timestamp and proves the canonical VanillaCord JAR byte-for-byte reproducible by comparing a validated build with a clean rebuild using the same effective inputs. Build timestamps remain excluded from the embedded manifest.

## Policy for automation

Automation must derive behavior from the checked-in POM, workflow, and `PROJECT_CONTRACT.json`, not from examples containing old CI run numbers. If documentation and executable build logic disagree, treat that as a documentation defect and fix the documentation through normal review rather than silently guessing.
