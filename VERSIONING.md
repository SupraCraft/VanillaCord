# VanillaCord versioning and provenance

VanillaCord and Bridge use independent versioning. VanillaCord never shares Bridge's version number; every build records the exact canonical Bridge coordinate it consumed.

## Canonical Maven identity

New artifacts from this fork use:

`io.github.supracraft.vanillacord:vanillacord:<version>`

The historical `net.ME1312:VanillaCord` coordinate identifies upstream/history and is not used for new SupraCraft artifacts. Java packages remain `vanillacord.*` because they are already neutral API/runtime names; changing them would add compatibility churn and impede upstream contribution without improving artifact ownership.

## Source and development versions

The checked-in POM is the single source of truth for the next release line and carries `X.Y.Z-dev`. Following upstream/fork release `v2.8`, the next normalized release line is `2.9.0`, so the checked-in development version is `2.9.0-dev`.

Ordinary CI appends the GitHub Actions run number:

`X.Y.Z-dev.<run-number>`

Example: `2.9.0-dev.81`.

These are immutable ordinary Maven versions. `SNAPSHOT` is intentionally not used. Earlier forms such as `2.9-SNAPSHOT.62` did not end in `-SNAPSHOT`, so Maven did not treat them as snapshots; the word added ambiguity without providing snapshot semantics.

## Release candidates and releases

Release candidates use `X.Y.Z-rc.N`. Stable releases use `X.Y.Z` and tags use `vX.Y.Z` going forward. Historical `v2.1` through `v2.8` tags remain valid history and are not rewritten.

A release build strips the leading `v` from its tag. After a stable release, the checked-in POM advances to the next intended `X.Y.Z-dev` line.

## Bridge relationship

Canonical Bridge coordinates use `io.github.supracraft.bridge`. Normal development CI may resolve the newest immutable `X.Y.Z-dev.N` Bridge build to expose integration failures early. The resulting exact coordinate is recorded in the manifest, SBOM, and build metadata.

Release builds do not float automatically. Unless an explicit `bridge_version` is provided, they use the exact Bridge version pinned in the source POM. This makes the release dependency input reconstructable without relying on repository `latest` metadata.

## Artifact filenames

The canonical standalone JAR is versioned and producer-qualified:

`supracraft-vanillacord-<version>.jar`

During migration, CI and releases also emit `VanillaCord.jar` as a temporary byte-identical compatibility alias for existing deployments. The alias is copied from the canonical artifact after the build; it is never compiled independently. New automation must consume the canonical filename or Maven coordinate.

The compatibility alias can be removed after known deployment consumers have migrated; its removal should be a deliberate compatibility change, not an incidental packaging cleanup.

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

CI additionally produces:

- `vanillacord-sbom.json` — CycloneDX dependency inventory
- `BUILD-METADATA.properties` — human/machine-readable identity and build inputs
- `ARTIFACT-INVENTORY.txt` — sorted JAR inventory
- `SHA256SUMS` — canonical JAR, compatibility alias, and SBOM hashes

## Reproducibility

Version strings identify release/development state, not source provenance. The Git commit, exact Bridge coordinate, Maven/wrapper versions, SBOM, and checksums carry reconstruction evidence separately. Build timestamps remain excluded from the embedded manifest; deterministic archive timestamps are handled by the separate reproducible-build modernization tranche.
