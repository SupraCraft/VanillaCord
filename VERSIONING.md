# VanillaCord versioning and provenance

VanillaCord and Bridge use independent versioning. VanillaCord does not share Bridge's version number; it records the exact Bridge Maven coordinate used to build each artifact.

## Source version

The checked-in POM is the single source of truth for the next VanillaCord development line and carries `<next-release>-SNAPSHOT`. The repository's established release sequence is `v2.1` through `v2.8`, so development following `v2.8` uses `2.9-SNAPSHOT`.

CI may rewrite the effective Maven version for an individual build without committing that generated value back to the repository. Workflow code derives the numeric base from the POM rather than duplicating it.

## CI versions

Ordinary non-tagged builds read the source POM, strip `-SNAPSHOT`, and use `<next-release>-SNAPSHOT.<GitHub run number>`. For the current development line this produces versions such as `2.9-SNAPSHOT.62`.

The JAR manifest also records the source Git commit, ref, and run number.

Development/PR builds may resolve the newest compatible Bridge snapshot when no explicit `BRIDGE_VERSION` is supplied. Once resolved, that exact version is passed to Maven and recorded in the artifact metadata and SBOM.

## Release versions

VanillaCord preserves its established `v<major>.<minor>` tag convention (for example `v2.8`). A patch component may be added if a future maintenance release needs one. The effective Maven/artifact version is the tag with the leading `v` removed.

The source POM must advance to the next intended development release after a release line is established; it must not remain on an unrelated historical Maven version.

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

Build timestamps are intentionally excluded from the embedded JAR manifest. Source commit, effective project version, exact Bridge version, and dependency SBOM provide the durable reconstruction inputs.
