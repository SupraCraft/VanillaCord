# VanillaCord diagnostics

VanillaCord keeps its operator-facing diagnostics intentionally small. The patcher CLI uses normal stdout/stderr and process exit status; it does not introduce a logging framework.

## Contract

Actionable CLI failures use a stable event identifier in square brackets. Human text may improve over time; automation and agents should key on the event identifier rather than exact prose.

| Event | Severity | Meaning |
| --- | --- | --- |
| `VC-E001` | error | No Minecraft version was supplied to the patcher CLI. |
| `VC-E002` | error | Requested Minecraft version metadata could not be resolved. |
| `VC-E003` | error | Downloaded Mojang version-profile metadata failed size or SHA-1 integrity validation. |
| `VC-E004` | error | Downloaded Minecraft server JAR failed size or SHA-1 integrity validation. |
| `VC-E999` | error | Unexpected patch/download failure not classified by a more specific event. |

Ordinary progress remains on stdout. Actionable failures are emitted on stderr and the process exits nonzero. The exception stack trace is retained on stderr after the stable event line so a human or agent has the underlying diagnostic context.

## Automation guidance

- Treat process exit code `0` as success and nonzero as failure.
- Parse stable event IDs from stderr for failure classification.
- Do not infer success/failure from progress prose on stdout.
- Preserve the full stderr stream when reporting an incident; the stable event ID identifies the class while the exception trace carries instance-specific detail.
- Minecraft server runtime logging is outside this CLI contract and remains owned by the patched Minecraft server/runtime.
