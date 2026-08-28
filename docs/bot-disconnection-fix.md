# Bot disconnection fix — historical incident record

Date: 2026-06-21

This document records a completed BungeeGuard defect investigation and fix. It is retained as engineering history and troubleshooting context; its original build/deploy commands are not current operational instructions. Use `README.md`, `AGENTS.md`, and `docs/compatibility.md` for current build and validation commands.

## Issue

Bots (and players) connecting through a **BungeeGuard**-configured VanillaCord backend server were being silently disconnected with a `NullPointerException` when their BungeeCord proxy did not include IP-forwarding properties in the handshake host field.

## Root cause

**File:** `java/vanillacord/server/BungeeHelper.java`, method `parseHandshake()`

The control flow for setting the `PROPERTIES_KEY` Netty channel attribute had two gaps when `seecrets != null` (BungeeGuard mode):

1. `split.length == 3` (no properties section): `PROPERTIES_KEY` was never set.
2. `split.length == 4` with an empty properties array: the attribute was only assigned inside the non-empty branch.

When `PROPERTIES_KEY` was unset, `injectProfile()` could obtain `null` and fail during property iteration. `QuietException` handling made the client-visible symptom look like a silent disconnect.

## Resolution

The BungeeGuard parsing path was changed so that missing or empty forwarded properties produce an explicit empty property array, ensuring the channel attribute is set consistently.

Defensive checks were also added in `injectProfile()` so missing UUID/property state produces an actionable forwarding error or an empty property set rather than an unexplained `NullPointerException`.

## Impact

- affected mode: BungeeGuard forwarding
- unaffected forwarding implementation: Velocity uses a different code path
- symptom: silent disconnect / hidden NPE
- diagnostic value: malformed or incomplete proxy forwarding data now fails more predictably

## Velocity review performed at the time

`VelocityHelper.completeTransaction()` was reviewed during the incident. Invalid transaction IDs, null data, and bad HMAC signatures terminated the connection through the expected exception path, and login state cleanup occurred in a `finally` block. No Velocity fix was required by this incident.

## Current verification guidance

For any regression related to this historical defect:

1. build with the pinned Maven Wrapper (`./mvnw -B verify` or `mvnw.cmd`);
2. preserve the artifact/reproducibility contracts described in `AGENTS.md`;
3. run the canonical compatibility sentinel as described in `docs/compatibility.md`;
4. test the specific BungeeGuard handshake/property edge case with focused regression coverage.

Do not deploy or reference the retired `artifacts/VanillaCord.jar` alias from older incident notes. Current standalone artifacts use `supracraft-vanillacord-<version>.jar`.
