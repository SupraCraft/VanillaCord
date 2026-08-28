## Summary

Describe the behavior, documentation, build, dependency, or compatibility change.

## Why

Explain the problem being solved and why this repository is the correct place to solve it. Link related issues when applicable.

## Contract impact

Check or describe every affected surface:

- [ ] runtime/patching behavior
- [ ] Minecraft compatibility surface
- [ ] Bridge dependency/integration
- [ ] artifact contents or filename
- [ ] Maven coordinates/version semantics
- [ ] provenance/SBOM/checksum/reproducibility evidence
- [ ] documentation/agent/automation contract
- [ ] no contract-affecting change

If artifact identity, versioning, or compatibility semantics change, update the corresponding focused documentation and `PROJECT_CONTRACT.json` where appropriate.

## Validation

List the exact checks run and their results. Relevant repository gates include:

- `./mvnw -B verify`
- artifact contract
- reproducibility proof
- legacy-alias absence
- current-stable Minecraft patch/integrity/boot
- deterministic forwarding/SourceScanner tests

Do not claim a gate passed unless there is corresponding local or CI evidence.

## Dependencies

List any dependency/plugin changes, including whether they are bundled, provided Minecraft-facing fixtures, Bridge inputs, or test-only dependencies. For authlib/Netty changes, identify the stable Minecraft evidence used to select the version.

## Upstream / compatibility notes

State whether the change is suitable to flow upstream, intentionally fork-specific, or has compatibility/rollback implications. Preserve SupraCraft producer identity and separate upstream lineage.
