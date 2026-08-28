# VanillaCord brand and public-surface notes

VanillaCord follows the SupraCraft candidate brand contract `0.1.0-candidate` using the `minecraft-server` family profile.

## Identity

The primary metaphor is a **warm vanilla-cream cord connecting a plain vanilla server endpoint to a proxy/network endpoint**. The cord is the recognizable product element.

Bridge is an implementation dependency and is intentionally absent from the user-facing mark.

## Palette

Canonical values live in `docs/assets/brand/brand.json`.

- vanilla cream — primary cord/light identity
- toasted vanilla — depth and secondary cable detail
- copper — connector/hardware accent
- grass and stone — restrained Minecraft-adjacent context
- cyan — forwarding/network activity
- cocoa — outlines and readable dark neutral

## Visual rules

- Use simple flat geometry rather than rendered fantasy scenery.
- Keep the cord visibly anchored between endpoints.
- Avoid isolated looped cable silhouettes that can become ambiguous at small sizes.
- Do not copy Minecraft textures, fonts, mobs, logos, or UI.
- Do not embed BungeeCord, Velocity, Paper, Bridge, or other ecosystem marks into VanillaCord's primary identity.
- Related-project logos may appear only as clearly attributed compatibility/reference marks when permission and need justify them.

## Copy

Preferred plain-language description:

> Connect vanilla Minecraft servers to proxies with forwarded player identity.

Technical documentation may describe the BungeeCord, BungeeGuard, and Velocity forwarding paths precisely. Avoid unsupported superlatives and avoid leading users through internal implementation dependencies before explaining the user-facing task.

## Assets

- `docs/assets/brand/icon.svg` — canonical vector mark
- `docs/assets/brand/hero.svg` — Pages/social hero illustration
- `docs/assets/brand/brand.json` — machine-readable identity manifest
- `src/main/resources/META-INF/supracraft/vanillacord/icon.svg` — packaged vector resource
- `src/main/resources/META-INF/supracraft/vanillacord/icon-128.png` — packaged raster resource for ordinary Java/launcher consumers

The raw JAR does not have a portable operating-system file-icon slot. Packaged resources exist for launchers, future UI code, wrappers, and native packaging.

## Public surface

GitHub Pages is generated from repository contracts. Human HTML remains concise and usable without JavaScript; automation and agents should prefer the generated JSON endpoints and `llms.txt`.
