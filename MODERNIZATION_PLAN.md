# VanillaCord build modernization plan

Last reviewed: 2026-08-28

## Objective

Modernize VanillaCord's build and packaging machinery without changing the runtime contract that the compatibility sentinel now proves. The goal is lower maintenance risk, reproducible artifacts, explicit toolchain constraints, and smaller build-system surface area—not novelty or wholesale migration.

The modernization must preserve these invariants:

- Java source/bytecode baseline remains Java 21 unless a separate compatibility decision changes it.
- GitHub compatibility probes may use newer JDKs when required by current Minecraft.
- `VanillaCord.jar` remains the operational release filename.
- `Main-Class: vanillacord.Downloader` remains present.
- artifact provenance remains embedded: VanillaCord version, source commit/ref/run, and exact Bridge version.
- CycloneDX SBOM, `BUILD-METADATA.properties`, and `SHA256SUMS` remain build evidence.
- `provided` Minecraft/runtime dependencies remain excluded from the fat JAR.
- current stable Minecraft patch + integrity + boot remains a required compatibility signal.
- deterministic Velocity forwarding-boundary and SourceScanner tests remain green.
- Bridge and VanillaCord remain independently versioned.

## Current baseline

As of this review:

- project development line: `2.9-SNAPSHOT`
- build JDK/source target: Java 21
- Maven Assembly Plugin: `2.2-beta-5`
- Maven Compiler Plugin: `3.13.0`
- Maven Surefire Plugin: `3.2.5`
- Versions Maven Plugin invoked by CI: `2.16.2`
- CycloneDX Maven Plugin: `2.9.3`
- Maven core on GitHub runners is not pinned by the repository
- `maven-antrun-plugin` is unpinned and is used only to copy `LICENSE`

Upstream versions checked on 2026-08-28:

- Maven GA: `3.9.16`; Maven 4 remains release-candidate software (`4.0.0-rc-6`)
- Maven Assembly Plugin: `3.8.0`
- Maven Compiler Plugin: `3.15.0`
- Maven Surefire stable line: `3.5.6` (do not adopt milestone `3.6.0-M1` as the baseline)
- Maven Antrun Plugin: `3.2.0`
- Maven Enforcer Plugin: `3.6.3`
- Maven Artifact Plugin: `3.6.1`
- Maven Shade Plugin: `3.6.2`
- Versions Maven Plugin: `2.21.0`
- CycloneDX Maven Plugin: `2.9.3` (already current)

Authoritative references:

- https://maven.apache.org/plugins/
- https://maven.apache.org/docs/history.html
- https://maven.apache.org/guides/mini/guide-reproducible-builds.html
- https://www.mojohaus.org/versions/versions-maven-plugin/
- https://github.com/CycloneDX/cyclonedx-maven-plugin/releases

## Decision principles

1. Modernize one failure domain at a time.
2. Prefer current GA/stable tools; do not put Maven 4 RCs or milestone plugins on the required path.
3. Preserve packaging semantics before attempting packaging redesign.
4. Make every migration prove artifact behavior, not merely `mvn verify` success.
5. Avoid coupled Bridge + VanillaCord upgrades unless the dependency boundary requires them.
6. Prefer deleting bespoke machinery over adding automation.
7. Do not automatically upgrade Minecraft-facing `provided` dependencies just because newer artifacts exist; they are compatibility interfaces, not ordinary bundled libraries.
8. Keep rollback to the preceding known-good POM/workflow commit trivial.

## Phase 0 — freeze and measure the contract

**Purpose:** create a precise baseline before changing build tools.

Add a small artifact-contract check (or extend the existing manifest check) that records/validates:

- executable JAR exists and is readable
- required manifest fields and main class
- exact Bridge coordinate
- expected bundled dependency classes are present
- representative `provided` dependency classes are absent
- LICENSE is present
- JAR entry inventory can be captured for comparison
- current stable patch + boot compatibility probe passes

For modernization PRs, retain the pre-change and post-change artifact inventories as CI evidence. A byte-for-byte match is desirable when feasible, but semantic equivalence is the initial acceptance criterion because newer archive tooling may legitimately alter ZIP metadata/order.

**Exit criterion:** baseline artifact contract is explicit enough to distinguish a packaging regression from harmless archive-format differences.

## Phase 1 — pin the build engine

**Recommended change:** add Maven Wrapper pinned to Maven `3.9.16` and use `./mvnw` in CI and documented local commands.

Add Maven Enforcer `3.6.3` with narrowly scoped rules:

- require Maven 3.9.x-compatible baseline
- require Java 21 or newer for the build
- optionally reject duplicate dependency declarations / bad convergence only after evaluating Bridge/Minecraft dependency behavior

Do not require Maven 4.

Why first: a repository cannot claim reproducible/maintainable Maven behavior while silently depending on whichever Maven happens to be installed on a runner or workstation.

**Acceptance:** wrapper build and current runner build produce semantically identical JARs and all compatibility tests pass.

## Phase 2 — remove obsolete packaging risk without redesign

Upgrade Maven Assembly Plugin directly from `2.2-beta-5` to current stable `3.8.0` **without changing the packaging model**.

Keep:

- `jar-with-dependencies`
- stable output filename
- generated manifest/provenance fields
- existing dependency scopes

Do not switch to Shade in the same PR.

Required evidence:

- full unit suite
- artifact-contract comparison against baseline
- `jar tf` integrity
- manifest assertions
- current stable Minecraft patch + boot
- deterministic forwarding-boundary tests
- SBOM still identifies the exact resolved Bridge version

If Assembly 3.8.0 changes inclusion semantics, fix the descriptor/configuration explicitly rather than falling back to the beta plugin.

**Rollback:** single POM version revert.

## Phase 3 — modernize ordinary Maven plugins

Use separate small PRs or one tightly scoped plugin-refresh PR after Phase 2 is stable:

- Compiler `3.13.0` → `3.15.0`
- Surefire `3.2.5` → stable `3.5.6`
- Versions Maven Plugin CI invocation `2.16.2` → `2.21.0`
- explicitly pin any remaining lifecycle helper plugins

CycloneDX `2.9.3` is already current; do not churn it merely for symmetry.

JUnit itself is a separate dependency migration. JUnit 6 is now GA, but a major test-framework upgrade provides little value to the production artifact and should not be bundled into build-tool modernization. Keep the existing JUnit line until a focused test-maintenance PR demonstrates a concrete benefit.

**Acceptance:** same artifact contract and compatibility gates as Phase 2; no new warnings or deprecated-plugin behavior in Maven logs.

## Phase 4 — delete unnecessary Ant machinery

The current Antrun execution exists only to copy `LICENSE` into build output. Replace it with ordinary Maven resource configuration (or another standard lifecycle-native mechanism), then remove `maven-antrun-plugin` entirely.

Do not merely upgrade Antrun to `3.2.0` unless replacement proves unexpectedly awkward. Deletion is the preferred modernization.

**Acceptance:** LICENSE remains in `VanillaCord.jar`; no other JAR entries change unexpectedly.

## Phase 5 — reproducible-build mode

After modern packaging plugins are in place, enable Maven reproducible-build behavior.

Recommended approach:

1. derive `SOURCE_DATE_EPOCH` / `project.build.outputTimestamp` from the source commit rather than wall-clock build time
2. ensure the archive plugins honor that value
3. configure CycloneDX reproducible output where supported
4. run two clean builds of the same commit with identical explicit Bridge input
5. compare output with Maven Artifact Plugin and SHA-256
6. use `diffoscope` only when hashes differ and the reason is not obvious

The release workflow should pin the exact Bridge version during a reproducibility test; a moving snapshot resolution cannot be part of a deterministic rebuild experiment.

Maven's official reproducible-build guidance recommends `project.build.outputTimestamp` and `artifact:compare`; follow that model rather than inventing a custom comparator.

**Target:** same source commit + same JDK major + same Maven wrapper + same exact Bridge coordinate produces the same release JAR hash.

## Phase 6 — evaluate Assembly versus Shade; default is to keep Assembly

Do **not** migrate to Maven Shade Plugin solely because Shade is newer or more fashionable.

Assembly remains appropriate if VanillaCord only needs to concatenate its runtime dependencies into one executable JAR. Shade `3.6.2` becomes justified only if evidence shows a need for capabilities such as:

- resource/service-file transformers
- package relocation to avoid dependency collisions
- precise include/exclude behavior Assembly cannot express cleanly
- a packaging defect that current Assembly cannot resolve

A Shade experiment must run side-by-side against Assembly and compare:

- class/resource inventory
- signatures / `META-INF` treatment
- manifest fields
- Bridge-transformed classes
- startup/patch behavior
- forwarding tests

If there is no material benefit, close the experiment and keep Assembly 3.8.0. Avoid creating maintenance work for theoretical cleanliness.

## Phase 7 — dependency modernization as a separate concern

Run deterministic update reports (`versions:display-dependency-updates` and `versions:display-plugin-updates`) manually or on a low-frequency workflow, but do not auto-merge upgrades.

Classify dependencies before changing them:

- **bundled implementation dependencies** (for example fastjson2, ASM): normal update candidates after tests
- **provided Minecraft/runtime APIs** (authlib, Netty): compatibility surfaces; update compile baselines only with multi-version evidence
- **Bridge**: independently versioned integration dependency; development can follow current snapshots, releases record/pin the exact coordinate
- **test-only dependencies**: lower runtime risk but still change separately from packaging

A dependency bump should not be hidden inside an Assembly/Maven upgrade PR.

## Phase 8 — Maven 4 readiness, not Maven 4 adoption

Maven 4 is still RC software as of this review. Do not make it required.

When Maven 4 reaches GA:

1. add a nonblocking Maven 4 CI lane
2. validate the Bridge Maven plugin specifically, because it is more likely than ordinary dependencies to depend on Maven internals/API behavior
3. run the same artifact and compatibility checks
4. observe several normal changes/releases
5. only then consider changing the wrapper/default from Maven 3.9.x

Bridge should receive an equivalent nonblocking Maven 4 compatibility lane before VanillaCord adopts Maven 4 as required infrastructure.

## CI structure during modernization

Keep the signal hierarchy simple:

- normal PR: Maven unit/build tests + artifact contract
- packaging/toolchain PR: normal PR checks + current stable Minecraft patch/boot
- scheduled compatibility sentinel: unchanged current stable + development-version policy
- release: full build evidence + exact dependency inputs + reproducibility check once proven reliable

Avoid adding a broad Maven/JDK matrix to every PR. Test only combinations tied to supported contracts.

## Proposed execution order

1. **Artifact contract baseline** — strengthen only what is needed for packaging comparison.
2. **Maven Wrapper 3.9.16 + Enforcer** — pin environment.
3. **Assembly 3.8.0** — retire the beta-era packaging plugin in isolation.
4. **Compiler/Surefire/Versions refresh** — current stable Maven-3-compatible releases.
5. **Remove Antrun** — replace LICENSE copy with standard resources.
6. **Reproducible build mode** — deterministic timestamp + two-build comparison.
7. **Dependency freshness review** — separate PRs by dependency class.
8. **Shade experiment only if evidence warrants it.**
9. **Maven 4 nonblocking lane after GA**, then reconsider default only after observation.

## Success criteria

The modernization is successful when:

- the project no longer relies on beta-era build plugins
- Maven and important plugins are explicitly pinned to supported GA versions
- the build has fewer bespoke/helper mechanisms
- artifact provenance/SBOM/checksums remain intact
- the same explicit inputs can reproduce the same release artifact
- compatibility evidence remains at least as strong as before modernization
- routine maintenance requires fewer judgment calls, not more

## Stop conditions

Pause or split a modernization step if:

- the change requires simultaneous runtime code changes to make the build pass
- packaging behavior cannot be explained from artifact diffs
- current stable Minecraft compatibility regresses
- Bridge compatibility becomes ambiguous
- the proposed tool introduces more custom configuration than it removes
- a migration's only argument is that a newer tool exists

When a step violates those conditions, preserve the last known-good build and open a narrowly scoped follow-up rather than forcing the migration through.
