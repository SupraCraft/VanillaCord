# Artifact and evidence retention policy

VanillaCord has several persistence classes. They are not interchangeable cleanup targets.

## GitHub Actions artifacts

Actions artifacts are transient validation evidence, not the permanent release record.

- Reproducibility-failure diagnostics are retained for 7 days.
- Ordinary validated build evidence is retained for 14 days.
- Minecraft compatibility reports are retained for 30 days because they are observational evidence across upstream Minecraft changes.
- Expiration of an Actions artifact does not alter a published release or its source history.

The executable retention values live in `.github/workflows/build.yml` and `.github/workflows/compatibility.yml`. `PROJECT_CONTRACT.json` exposes the same values for automation, and the documentation contract verifies that they remain synchronized.

## GitHub Releases

Release tags and release assets are durable historical provenance. Do not delete, rename, or rewrite an old release merely because current artifact identity or naming policy has changed.

Older releases may legitimately contain the historical `VanillaCord.jar` filename. That filename is forbidden for current output, but its presence in historical releases is evidence of what was actually published at the time.

## Bridge package dependencies

VanillaCord consumes exact immutable Bridge coordinates. Those package versions are dependencies and reproducibility inputs, not VanillaCord-owned transient cache entries.

Package-retention and deletion policy belongs to `SupraCraft/Bridge`. VanillaCord must not assume that an old Bridge `dev.<run>` coordinate is disposable merely because a newer one exists. Source-pinned release inputs and maintained refs must remain reproducible.

## Cleanup boundary

Do not add broad cleanup machinery unless retained state creates a concrete operational or storage burden. Any future destructive cleanup must inventory exact candidates, preserve durable release evidence and referenced dependencies, dry-run before mutation, and re-check live state immediately before deletion so drift fails closed.
