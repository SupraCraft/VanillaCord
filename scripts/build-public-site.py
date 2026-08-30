#!/usr/bin/env python3
"""Build VanillaCord's end-user and machine-readable GitHub Pages surfaces."""

import argparse
import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SOURCE_URL = "https://github.com/SupraCraft/VanillaCord"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def external_link(url, label, css_class=""):
    classes = " ".join(item for item in (css_class, "external-link") if item)
    return (
        f'<a class="{html.escape(classes, quote=True)}" '
        f'href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">'
        f'{html.escape(label)} '
        '<span class="external-link-indicator" aria-hidden="true">↗</span>'
        '<span class="sr-only"> (opens in a new tab or window)</span>'
        '</a>'
    )


def primary_nav(base, active):
    items = [
        ("download", "Download", "download/"),
        ("support", "Supported versions", "support/"),
        ("guide", "Guide", "guide/"),
        ("releases", "Releases", "releases/"),
    ]
    links = []
    for key, label, route in items:
        current = ' aria-current="page"' if active == key else ""
        links.append(f'<a href="{base}/{route}"{current}>{label}</a>')
    return "".join(links)


def shell(title, description, body, base, canonical_base, active):
    canonical_route = {
        "download": "download/",
        "support": "support/",
        "guide": "guide/",
        "releases": "releases/",
        "accessibility": "accessibility/",
    }.get(active, "")
    canonical = canonical_base + "/" + canonical_route
    brand_current = ' aria-current="page"' if active == "home" else ""
    accessibility_current = ' aria-current="page"' if active == "accessibility" else ""
    source = external_link(SOURCE_URL, "Source")
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} · VanillaCord</title>
  <meta name="description" content="{html.escape(description, quote=True)}">
  <link rel="canonical" href="{html.escape(canonical, quote=True)}">
  <link rel="icon" href="{base}/assets/brand/icon.svg" type="image/svg+xml">
  <meta name="color-scheme" content="light dark">
  <meta name="theme-color" content="#F1E2BF">
  <script src="{base}/assets/site.js"></script>
  <link rel="stylesheet" href="{base}/assets/site.css">
</head>
<body>
<a class="skip-link" href="#main-content">Skip to main content</a>
<header class="site-header"><div class="shell"><nav class="site-nav" aria-label="Primary"><a class="brand" href="{base}/"{brand_current}><img class="brand-mark" src="{base}/assets/brand/icon.svg" alt="" aria-hidden="true"><span>VanillaCord</span></a><div class="nav-cluster"><div class="nav-links">{primary_nav(base, active)}</div><label class="theme-control" for="theme-select"><span>Theme</span><select id="theme-select" aria-label="Color theme"><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select></label></div></nav></div></header>
<main id="main-content" class="shell" tabindex="-1">{body}</main>
<footer class="site-footer"><div class="shell footer-row"><span>VanillaCord · SupraCraft · MPL-2.0</span><span><a href="{base}/accessibility/"{accessibility_current}>Accessibility</a> · {source}</span></div></footer>
</body>
</html>'''


def state(status):
    return {
        "pass": '<span class="status-dot status-pass" aria-hidden="true"></span>Supported',
        "fail": '<span class="status-dot status-fail" aria-hidden="true"></span>Failed qualification',
    }.get(status, '<span class="status-dot status-unknown" aria-hidden="true"></span>Not recorded for this release')


def support_table(supported, evidence):
    found = {item.get("version"): item for item in evidence or []}
    rows = []
    for target in supported["targets"]:
        result = found.get(target["version"], {})
        rows.append(
            f'<tr><td>{state(result.get("status"))}</td>'
            f'<td><code>{html.escape(target["version"])}</code></td>'
            f'<td>{html.escape(target["generation"])}</td>'
            f'<td>Java {int(target["java"])}</td></tr>'
        )
    return "".join(rows)


def support_table_html(supported, evidence, caption):
    return (
        '<div class="table-scroll" role="region" aria-label="Minecraft compatibility table" tabindex="0">'
        '<table>'
        f'<caption>{html.escape(caption)}</caption>'
        '<thead><tr><th scope="col">State</th><th scope="col">Minecraft</th><th scope="col">Generation</th><th scope="col">Runtime</th></tr></thead>'
        f'<tbody>{support_table(supported, evidence)}</tbody></table></div>'
    )


def release_html(release, supported, base, canonical_base):
    artifact = release["artifact"]
    version = release["version"]
    checksum = artifact.get("sha256") or "See release checksums"
    bridge = f'<p><strong>Bridge:</strong> <code>{html.escape(release["bridge_version"])}</code></p>' if release.get("bridge_version") else ""
    table = support_table_html(supported, release.get("minecraft_support", []), f"Minecraft qualification for VanillaCord {version}")
    download = external_link(artifact["download_url"], f'Download {artifact["name"]}', "button primary")
    body = f'''<div class="eyebrow">Stable release</div><h1>VanillaCord {html.escape(version)}</h1><p>{html.escape(release.get("summary", "Stable VanillaCord release."))}</p><div class="card"><h2>Download</h2><p>{download}</p><p class="quiet">SHA-256: <code>{html.escape(checksum)}</code></p>{bridge}</div><h2>Supported Minecraft releases</h2><p>Supported means this release patched the Mojang server, produced a readable JAR, and booted it on the listed Java runtime during stable qualification.</p>{table}<div class="card"><h2>Automation</h2><div class="link-list"><a href="{base}/releases/stable.json">stable.json</a><a href="{base}/releases/stable.txt">stable.txt</a><a href="{base}/releases/stable-url.txt">stable-url.txt</a></div></div>'''
    return shell(
        f"Release {version}",
        f"VanillaCord {version} release downloads, checksums, and Minecraft compatibility evidence.",
        body,
        base,
        canonical_base,
        "releases",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="build/public-site")
    parser.add_argument("--base-url", help="Override navigational base URL for local browser testing.")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output)
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(DOCS, output)

    contract = load(ROOT / "PROJECT_CONTRACT.json")
    metadata = load(ROOT / "GITHUB_METADATA.json")
    brand = load(DOCS / "assets/brand/brand.json")
    stable = load(ROOT / "STABLE_RELEASE.json")
    supported = load(ROOT / "SUPPORTED_MINECRAFT.json")
    canonical_base = metadata["homepage"].rstrip("/")
    base = (args.base_url or canonical_base).rstrip("/")
    manifests = [load(p) for p in sorted((ROOT / "release-manifests").glob("*.json"))] if (ROOT / "release-manifests").is_dir() else []
    if not any(r.get("version") == stable["version"] for r in manifests):
        manifests.append(stable)

    write_json(output / "project.json", contract)
    write_json(output / "github.json", metadata)
    write_json(output / "brand.json", brand)
    write_json(output / "releases/stable.json", stable)
    write(output / "releases/stable.txt", stable["version"] + "\n")
    write(output / "releases/stable-url.txt", stable["artifact"]["download_url"] + "\n")
    write(output / "releases/stable-sha256.txt", (stable["artifact"].get("sha256") or "") + "\n")
    support_endpoint = {
        "schema": "vanillacord-public-support-matrix/1",
        "stable_release": stable["version"],
        "policy": supported["policy"],
        "selection": supported["selection"],
        "targets": supported["targets"],
        "results": stable.get("minecraft_support", []),
    }
    write_json(output / "support-matrix.json", support_endpoint)
    write_json(
        output / "artifacts.json",
        {
            "schema_version": "1.1.0",
            "repository": contract["repository"],
            "source_version": contract["source_version"],
            "stable_release": stable,
            "artifact": contract["artifact"],
            "versioning": contract["versioning"],
            "provenance": contract["provenance"],
        },
    )
    write_json(
        output / "compatibility.json",
        {
            "schema_version": "1.1.0",
            "repository": contract["repository"],
            "tiers": contract["validation"]["compatibility_tiers"],
            "human_support_matrix": base + "/support/",
            "machine_support_matrix": base + "/support-matrix.json",
            "stable_release": stable["version"],
            "note": "This endpoint describes compatibility policy and authoritative support locations; it does not assert that every Minecraft version is supported without release-specific evidence. Release-specific green/red state is published in support-matrix.json and the human support page.",
        },
    )

    artifact = stable["artifact"]
    version = stable["version"]
    checksum = artifact.get("sha256") or "See release checksums"
    download = external_link(artifact["download_url"], f'Download {artifact["name"]}', "button primary")
    download_body = f'''<div class="eyebrow">Current stable</div><h1>Download VanillaCord {html.escape(version)}</h1><p>For most server operators, this is the release to use.</p><div class="card"><h2>Stable JAR</h2><div class="actions">{download}<a class="button" href="{base}/releases/{html.escape(version)}/">Release details</a></div><p class="quiet">SHA-256: <code>{html.escape(checksum)}</code></p></div><h2>Run the patcher</h2><pre><code>java -jar {html.escape(artifact["name"])} &lt;minecraft-version&gt;</code></pre><p>Patched servers are written under <code>out/</code>. Check the <a href="{base}/support/">supported-version matrix</a> for the target runtime, then continue with the <a href="{base}/guide/">setup guide</a>.</p><div class="notice"><strong>Security:</strong> proxy forwarding changes how backend identity is trusted. Firewall the backend server so players cannot connect around the proxy.</div>'''
    write(output / "download/index.html", shell("Download", f"Download the current stable VanillaCord release {version}, checksum, and release details.", download_body, base, canonical_base, "download"))

    current_target = next((target for target in supported["targets"] if target.get("current")), supported["targets"][0])
    current_mc = html.escape(current_target["version"])
    bash_example = f'''VERSION=$(curl -fsSL {base}/releases/stable.txt)\nURL=$(curl -fsSL {base}/releases/stable-url.txt)\ncurl -fL "$URL" -o "vanillacord-$VERSION.jar"'''
    ps_example = f'''$version = (Invoke-RestMethod '{base}/releases/stable.txt').Trim()\n$url = (Invoke-RestMethod '{base}/releases/stable-url.txt').Trim()\nInvoke-WebRequest $url -OutFile "vanillacord-$version.jar"'''
    guide_body = f'''<div class="eyebrow">End-user guide</div><h1>Set up VanillaCord</h1><h2>1. Check support</h2><p>Start with the <a href="{base}/support/">supported-version matrix</a>. It records the Java runtime used when each Minecraft generation was qualified.</p><h2>2. Download VanillaCord</h2><p>Get the <a href="{base}/download/">current stable release</a> and verify its published checksum when your deployment process requires artifact verification.</p><h2>3. Patch your Minecraft release</h2><pre><code>java -jar {html.escape(artifact["name"])} {current_mc}</code></pre><p>Replace <code>{current_mc}</code> with another supported target when needed.</p><h2>4. Run the patched backend</h2><pre><code>java -Xms2G -Xmx2G -jar out/{current_mc}.jar --nogui</code></pre><h2>5. Configure proxy forwarding</h2><p>Choose Velocity, BungeeCord, or BungeeGuard forwarding in <code>vanillacord.txt</code> and use the matching proxy configuration. Keep the backend port firewalled so players cannot bypass the proxy.</p><h2>Automation examples</h2><h3>Bash / Linux</h3><pre><code>{html.escape(bash_example)}</code></pre><h3>PowerShell</h3><pre><code>{html.escape(ps_example)}</code></pre><p>Structured consumers can use <a href="{base}/releases/stable.json">stable.json</a> and <a href="{base}/support-matrix.json">support-matrix.json</a>.</p>'''
    write(output / "guide/index.html", shell("Guide", "Set up VanillaCord, patch a supported Minecraft server, configure proxy forwarding, and automate stable downloads.", guide_body, base, canonical_base, "guide"))

    table = support_table_html(supported, stable.get("minecraft_support", []), f"Supported Minecraft releases for stable VanillaCord {version}")
    support_body = f'''<div class="eyebrow">Compatibility</div><h1>Supported Minecraft releases</h1><p>{html.escape(supported["policy"])}</p><p class="quiet">Current stable VanillaCord: <a href="{base}/releases/{html.escape(version)}/">{html.escape(version)}</a>. “Not recorded” means the stable release metadata predates the current structured qualification record; it is not a green support claim.</p>{table}<div class="card"><h2>For automation</h2><p><a href="{base}/support-matrix.json">support-matrix.json</a></p></div>'''
    write(output / "support/index.html", shell("Supported versions", "Evidence-backed Minecraft and Java runtime compatibility for the current stable VanillaCord release.", support_body, base, canonical_base, "support"))

    links = []
    for release in sorted(manifests, key=lambda r: r["version"], reverse=True):
        release_dir = output / f"releases/{release['version']}"
        write(release_dir / "index.html", release_html(release, supported, base, canonical_base))
        suffix = " — current stable" if release["version"] == version else ""
        links.append(f'<li><a href="{base}/releases/{html.escape(release["version"])}/">VanillaCord {html.escape(release["version"])}</a>{suffix}</li>')
    releases_body = '<div class="eyebrow">Release history</div><h1>VanillaCord releases</h1><ul>' + "".join(links) + '</ul><p>GitHub remains the developer/source record; normal operator download and information flows stay on this site. Use the secondary Source link in the footer when repository access is actually needed.</p>'
    write(output / "releases/index.html", shell("Releases", "Browse VanillaCord release information and the current stable release.", releases_body, base, canonical_base, "releases"))

    accessibility_body = f'''<div class="eyebrow">Inclusive access</div><h1>Accessibility</h1><p>VanillaCord’s public site targets <strong>WCAG 2.2 Level AA</strong> and is designed to align with Revised Section 508 web accessibility criteria where applicable.</p><h2>Features</h2><ul><li>Semantic page landmarks, a skip-to-content link, structured headings, and accessible table markup.</li><li>Keyboard-visible focus indicators and primary navigation that remains available at narrow and zoomed layouts.</li><li>A Light / Dark / System control. System follows the browser or operating-system color preference; an explicit choice is stored locally in this browser.</li><li>Reduced-motion and forced-colors support using platform preferences.</li><li>External links use a visible ↗ indicator plus an assistive-technology notification and preserve this site in the current browsing context.</li></ul><h2>Testing</h2><p>Pull requests that change the public surface run deterministic route/link checks plus headless browser tests across desktop, 320-pixel reflow, light/dark preference handling, keyboard navigation, and automated WCAG A/AA checks. Automated tools cannot prove full accessibility or Section 508 conformance, so manual review remains part of release readiness for changes that materially alter interaction or content.</p><h2>Report a problem</h2><p>If something on this site is difficult to use with a keyboard, screen reader, zoom, high-contrast mode, or another assistive technology, use the secondary Source link in this page footer to reach the currently available project feedback or contribution channel. Include the affected page, browser/assistive technology if known, and what blocked you.</p>'''
    write(output / "accessibility/index.html", shell("Accessibility", "Accessibility features, testing target, and feedback path for the VanillaCord public site.", accessibility_body, base, canonical_base, "accessibility"))

    write(output / "llms.txt", f'''# VanillaCord\n\nCanonical human entry point: {base}/\nDownload: {base}/download/\nGuide: {base}/guide/\nSupported releases: {base}/support/\nAccessibility: {base}/accessibility/\nCurrent stable JSON: {base}/releases/stable.json\nCurrent stable version: {base}/releases/stable.txt\nCurrent stable artifact URL: {base}/releases/stable-url.txt\nSupport matrix JSON: {base}/support-matrix.json\nProject contract: {base}/project.json\nRepository: https://github.com/{contract['repository']}\nUpstream: https://github.com/{contract['upstream_repository']}\n\nPrefer these endpoints over scraping presentation HTML or GitHub release pages.\n''')


if __name__ == "__main__":
    main()
