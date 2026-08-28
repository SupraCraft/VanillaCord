# Bridge dependency

VanillaCord still depends on Bridge; it is an active build/runtime transformation dependency, not a historical leftover.

## Canonical dependency identity

The maintained producer is `SupraCraft/Bridge`, a public fork of `ME1312/Bridge`.
New Bridge packages from the maintained fork use the canonical Maven group
`io.github.supracraft.bridge`. Historical `net.ME1312.ASM` packages identify the
upstream lineage and must not be used by new VanillaCord builds.

VanillaCord uses Bridge in three places:

| Use | Canonical dependency | Why it matters |
| --- | --- | --- |
| Build-time bytecode transformation | `io.github.supracraft.bridge:bridge-plugin` | Runs the Maven `bridge:bridge` goal during the VanillaCord build. |
| ASM helper APIs | `io.github.supracraft.bridge:bridge-asm` | Provides hierarchy scanning, writer, type-map, known-type, visitor, and bytecode helpers used by the patcher. |
| Bridge runtime API surface | `io.github.supracraft.bridge:bridge` | Provides `bridge.Invocation` and `bridge.Unchecked`, referenced by VanillaCord helpers and processed by the Bridge plugin. |

The Java `bridge.*` package names remain intentionally unchanged. They are neutral API names and retaining them avoids unnecessary binary/source churn while preserving the ability to flow suitable changes upstream.

## Package and version policy

Canonical Bridge development builds are immutable:

```text
io.github.supracraft.bridge:bridge:0.1.0-dev.34
io.github.supracraft.bridge:bridge-asm:0.1.0-dev.34
io.github.supracraft.bridge:bridge-plugin:0.1.0-dev.34
```

`0.1.0-dev.34` was the first canonical Bridge build published from the migrated master branch. Later normal integration CI may resolve a newer `X.Y.Z-dev.N` build, but each VanillaCord artifact records the exact coordinate it actually consumed.

The VanillaCord source POM pins a known exact Bridge baseline. Release builds use that source-pinned version unless an explicit exact `BRIDGE_VERSION` override is supplied. Development CI may use `scripts/resolve-bridge-version.sh`, which intentionally filters out legacy snapshots, release candidates, and stable versions and chooses only canonical immutable `X.Y.Z-dev.N` builds.

## Repository relationship

Maintained fork:

```text
https://github.com/SupraCraft/Bridge
```

Upstream:

```text
https://github.com/ME1312/Bridge
```

VanillaCord resolves Bridge through Maven packages, not a source checkout. The default package owner is `SupraCraft`; `BRIDGE_OWNER` can override the repository owner when deliberately testing another compatible publication source.

The produced VanillaCord manifest/build metadata preserves both identities separately:

```text
Bridge-Coordinate: io.github.supracraft.bridge:bridge:<exact-version>
Source-Repository: SupraCraft/VanillaCord
Upstream-Repository: ME1312/VanillaCord
```

Bridge JARs likewise record `SupraCraft/Bridge` as source and `ME1312/Bridge` as upstream.

## Submodule decision

Do not add Bridge as a Git submodule merely to tighten coupling.

- VanillaCord consumes versioned Maven artifacts.
- CI and local builds already exercise the same package path used by downstream consumers.
- A submodule would add a second dependency mechanism rather than replacing one.
- Exact immutable coordinates plus provenance provide a cleaner reproducibility boundary.
- Sibling source checkouts can still be used for coordinated development without becoming a release dependency.

Removing Bridge itself would be a separate architecture refactor. It would need to replace the hierarchy scanner, class-writer behavior, type-map helpers, and invocation transformations; it is not part of artifact-identity modernization.
