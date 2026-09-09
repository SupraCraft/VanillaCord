# VanillaCord Minecraft compatibility status

This repository does **not** keep a manually curated evergreen compatibility-result table in Git.

Current compatibility evidence is produced by `.github/workflows/compatibility.yml` and the canonical `scripts/check-minecraft-compatibility.sh` probe. The workflow job summary and uploaded report artifact are authoritative for a specific run because they resolve Mojang's current release/development versions at execution time and record the exact VanillaCord artifact being tested.

Static compatibility tables become stale quickly and can mislead humans or automation. Do not infer current support from historical generated output committed to the repository.

## Current policy

- `current-stable`: blocking; patch + integrity + configured boot validation
- `required-supported`: blocking when explicitly requested
- `current-development`: advisory
- `best-effort`: advisory

See `../COMPATIBILITY_STRATEGY.md` for rationale and `compatibility.md` for the executable interface.

## Generating a report locally

Choose a transient output path when you do not intend to preserve a dated validation record:

```sh
export VANILLACORD_COMPAT_REPORT=/tmp/vanillacord-compatibility.md
scripts/check-minecraft-compatibility.sh
```

A generated report records its timestamp, Mojang manifest, resolved current versions, exact tested JAR, tier policy, and result. If a generated report is ever committed as evidence for a specific incident or release, label it explicitly as a dated historical record rather than updating this status page to look evergreen.
