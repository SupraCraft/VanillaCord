# Artifact identity and versioning

VanillaCord in this repository is a SupraCraft-maintained fork. Published artifacts must identify SupraCraft as the producer while preserving upstream attribution and keeping source changes straightforward to contribute upstream.

## Identity policy

Published Maven coordinates are owned by this repository, not by the upstream project.

Canonical coordinates:

- group: `io.github.supracraft.vanillacord`
- artifact: `vanillacord`

The legacy `net.ME1312:VanillaCord` coordinate is upstream-derived and is not the canonical identity for new SupraCraft builds.

The existing `vanillacord.*` Java implementation packages are already neutral. Do not rename Java packages merely to brand the fork; that would create large source diffs and make upstream flow-back harder without improving artifact identity.

Bridge dependencies consume SupraCraft-owned `io.github.supracraft.bridge` coordinates.

## Artifact metadata

Every distributable artifact records at least:

- `Implementation-Vendor: SupraCraft`
- source repository: `SupraCraft/VanillaCord`
- exact source commit
- exact VanillaCord version
- exact Bridge coordinate/version consumed
- upstream repository/base reference when known

CycloneDX metadata and release evidence carry the same source identity.

The canonical standalone release filename is:

- `supracraft-vanillacord-<version>.jar`

The historical `VanillaCord.jar` compatibility alias was retired before the normalized SupraCraft `2.9.0` release line. New CI artifacts and releases emit only the explicit, versioned SupraCraft filename. Historical releases may retain older upstream-derived filenames and remain historical evidence; they are not the naming contract for new artifacts.

## Version policy

Maven requires a version but does not require `SNAPSHOT`. The suffix `-SNAPSHOT` has special mutable repository semantics only when it is the actual suffix of the version.

Do not publish versions such as `2.9-SNAPSHOT.76`; Maven treats them as ordinary unique versions even though their names imply snapshot semantics.

Use these channels instead:

- source/development line: `2.9.0-dev`
- immutable main-branch CI build: `2.9.0-dev.<github-run-number>`
- release candidate: `2.9.0-rc.<n>`
- release: `2.9.0`

The exact Git SHA belongs in provenance metadata, not in the version string. Release builds must consume an exact immutable Bridge version. Integration CI may resolve the newest Bridge `-dev.<run>` version, but must record the exact coordinate it consumed.

## Upstream relationship

Do not encode upstream ownership in the published group ID or release filename. Preserve upstream attribution in README/license/NOTICE/source metadata and record the upstream base tag or commit independently from the SupraCraft artifact version. Fork identity and upstream lineage are separate machine-readable facts.
