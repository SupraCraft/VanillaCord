# VanillaCord versioning and provenance

VanillaCord and Bridge use independent semantic versioning. VanillaCord does not share Bridge's version number; it records the exact Bridge Maven coordinate used to build each artifact.

## Source version

The checked-in POM carries the next development version. CI may rewrite the effective Maven version for an individual build without committing that generated value back to the repository.

## CI versions

Ordinary non-tagged builds use `0.1.0-SNAPSHOT.<GitHub run number>`. The JAR manifest also records the Git commit, ref, and run number.

Development/PR builds may resolve the newest compatible Bridge snapshot when no explicit `BRIDGE_VERSION` is supplied. Once resolved, that exact version is passed to Maven and recorded in the artifact metadata and SBOM.

## Release versions

Release tags use `vX.Y.Z`; the effective Maven/artifact version is `X.Y.Z`.

For maximum rebuild reproducibility, a release may be invoked with an explicit exact `bridge_version`. If it is omitted, CI resolves Bridge once and records that exact resolved coordinate in all release provenance assets. A later rebuild can then supply the recorded value explicitly.

## Artifact identity

`VanillaCord.jar` retains its stable filename for operational compatibility. The artifact itself records:

- `Implementation-Title`
- `Implementation-Version`
- `Implementation-Vendor`
- `Build-Commit`
- `Build-Ref`
- `Build-Number`
- `Bridge-Version`

CI additionally produces:

- `vanillacord-sbom.json` — CycloneDX dependency inventory
- `BUILD-METADATA.properties` — compact human/machine-readable build inputs
- `SHA256SUMS` — hashes for the JAR and SBOM

Release builds attach these beside `VanillaCord.jar`.

## Bridge relationship

Normal development intentionally allows a moving Bridge snapshot so integration failures surface early. Releases are auditable because the exact resolved Bridge coordinate is persisted. Bridge/VanillaCord lockstep releases are explicitly avoided; compatibility is expressed by dependency coordinates plus CI tests.

## Reproducibility

Build timestamps are intentionally excluded from the embedded manifest. Source commit, effective project version, exact Bridge version, and dependency SBOM provide the durable reconstruction inputs.
