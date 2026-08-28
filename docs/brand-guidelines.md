# VanillaCord brand and public-surface notes

VanillaCord implements the SupraCraft organization brand contract as a project-specific Minecraft/server-tooling profile. The vendored snapshot is `BRAND_PROFILE.json`; the private governance repository is a design/governance source, never a normal build or runtime dependency.

## Identity

The central visual idea is a **vanilla-cream cord connecting a plain vanilla server endpoint to a proxy/network endpoint**.

- The cord must remain the most recognizable part of the mark.
- Cream/ivory expresses both vanilla flavor and the plain/stock meaning of vanilla Minecraft.
- Copper connector hardware provides a small shared SupraCraft family cue.
- Cyan may indicate network activity; grass/stone may provide restrained Minecraft-adjacent context.
- Bridge is an implementation dependency and must not be depicted as part of the user-facing identity.

The icon is intentionally endpoint-anchored. Do not turn it into a free-standing loop, knot, or ambiguous organic silhouette.

## Minecraft relationship

VanillaCord may use block-inspired geometry and warm server-world cues, but must not copy Minecraft textures, logos, fonts, mobs, interface elements, or other proprietary trade dress. Compatibility references to Velocity, BungeeCord, and BungeeGuard are factual text, not a reason to absorb their logos into the VanillaCord mark.

## Tone

Keep copy brief, practical, and factual. Prefer concrete statements such as “patch vanilla Minecraft server JARs for proxy forwarding” over promotional claims. Avoid superlatives and unsupported security/performance language.

Child-friendly means clear, non-hostile, and understandable—not cartoonish or simplified beyond technical truth.

## Canonical project assets

- `docs/assets/brand/icon.svg` — public primary mark and favicon.
- `docs/assets/brand/hero.svg` — wider Pages/social illustration.
- `docs/assets/brand/brand.json` — public machine-readable brand manifest.
- `resources/META-INF/supracraft/vanillacord/icon.svg` — same primary mark bundled as a classpath resource in the JAR.

The website and JAR copies of the primary icon must remain byte-for-byte identical.

## Pages information architecture

The public page should answer, in order:

1. What VanillaCord does.
2. Whether it is intended for the visitor’s type of server.
3. How to get/run it.
4. Where compatibility and forwarding information lives.
5. The backend-port/firewall safety boundary.
6. Where releases, source, and deeper documentation live.
7. Which generated endpoints automation and agents should consume.

The site must remain useful without JavaScript. Machine consumers should prefer generated JSON/agent endpoints over scraping presentation HTML.

## Organization lifecycle

This implementation currently tracks SupraCraft brand contract `0.1.0-candidate`. Future organization-brand changes are adopted through an explicit project change/PR; the project must never pull mutable branding from the private governance repository during a normal build.
