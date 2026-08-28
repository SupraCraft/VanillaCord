# Bridge dependency

VanillaCord depends on Bridge as an active build/transformation dependency, not as a historical leftover.

## Canonical dependency identity

The maintained producer is `SupraCraft/Bridge`, a public fork of `ME1312/Bridge`. Current Bridge packages use Maven group `io.github.supracraft.bridge`; historical `net.ME1312.ASM` packages identify upstream lineage and must not be used by new VanillaCord builds.

VanillaCord uses Bridge in three places:

| Use | Canonical dependency | Why it matters |
| --- | --- | --- |
| Build-time transformation | `io.github.supracraft.bridge:bridge-plugin` | Runs the Maven `bridge:bridge` goal during the VanillaCord build. |
| ASM helper APIs | `io.github.supracraft.bridge:bridge-asm` | Provides hierarchy/type/writer/visitor helpers used by the patcher. |
| Bridge API surface | `io.github.supracraft.bridge:bridge` | Provides Bridge runtime/API types referenced by VanillaCord helpers and processed by the plugin. |

The Java `bridge.*` package names remain intentionally unchanged. They are neutral API names and retaining them avoids unnecessary binary/source churn while preserving upstream-flowability.

## Version policy

Use one exact Bridge version across the related modules for a build:

```text
io.github.supracraft.bridge:bridge:<version>
io.github.supracraft.bridge:bridge-asm:<version>
io.github.supracraft.bridge:bridge-plugin:<version>
```

The VanillaCord source POM pins a known exact Bridge baseline. Development integration CI may use `scripts/resolve-bridge-version.sh` to select the newest canonical immutable `X.Y.Z-dev.N` build. Every produced VanillaCord artifact records the exact coordinate it actually consumed.

Release and reproducibility work must use an exact immutable Bridge coordinate rather than resolving again.

## Repository relationship

Maintained fork:

```text
https://github.com/SupraCraft/Bridge
```

Upstream:

```text
https://github.com/ME1312/Bridge
```

VanillaCord resolves Bridge through Maven packages, not a source checkout. `BRIDGE_OWNER` defaults to `SupraCraft`; override it only when deliberately testing another compatible publication source.

Produced VanillaCord provenance keeps producer and upstream lineage separate:

```text
Bridge-Coordinate: io.github.supracraft.bridge:bridge:<exact-version>
Source-Repository: SupraCraft/VanillaCord
Upstream-Repository: ME1312/VanillaCord
```

Bridge JARs similarly record `SupraCraft/Bridge` as source and `ME1312/Bridge` as upstream.

## Publication trust boundary

Bridge's current CI uses a build-once/promote-tested-bytes model: the package publication job deploys the exact JARs and version-set POMs produced and validated by the build job rather than rebuilding the reactor. This gives VanillaCord a cleaner reproducibility boundary when it pins an exact Bridge coordinate.

## Submodule decision

Do not add Bridge as a Git submodule merely to tighten coupling.

- VanillaCord consumes versioned Maven artifacts.
- CI/local builds exercise the same package path used by downstream consumers.
- A submodule would add a second dependency mechanism rather than replacing one.
- Exact immutable coordinates plus provenance provide the reproducibility boundary.
- Sibling source checkouts remain useful for coordinated development without becoming release dependencies.

Removing Bridge itself would be a separate architecture refactor. It would need to replace the hierarchy scanner, class-writer behavior, type-map helpers, and invocation transformations; it is not part of routine build modernization.
