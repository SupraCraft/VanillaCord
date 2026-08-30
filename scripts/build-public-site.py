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


def join_url(base, path=""):
    base = base.rstrip("/")
    path = path.lstrip("/")
    return f"{base}/{path}" if path else f"{base}/"


def internal_link(base, path, label, action, css_class="", current=False):
    class_attr = f' class="{html.escape(css_class, quote=True)}"' if css_class else ""
    current_attr = ' aria-current="page"' if current else ""
    return (
        f'<a{class_attr} href="{html.escape(join_url(base, path), quote=True)}" '
        f'data-surface-action="{html.escape(action, quote=True)}"{current_attr}>'
        f'{html.escape(label)}</a>'
    )


def resource_link(base, path, label, action):
    return internal_link(base, path, label, action)


def external_link(url, label, action, handoff, css_class=""):
    classes = " ".join(item for item in (css_class, "external-link") if item)
    return (
        f'<a class="{html.escape(classes, quote=True)}" '
        f'href="{html.escape(url, quote=True)}" '
        f'data-surface-action="{html.escape(action, quote=True)}" '
        f'data-surface-handoff="{html.escape(handoff, quote=True)}" '
        'target="_blank" rel="noopener noreferrer">'
        f'{html.escape(label)} '
        '<span class="external-link-indicator" aria-hidden="true">↗</span>'
        '<span class="sr-only"> (opens in a new tab or window)</span>'
        '</a>'
    )


def primary_nav(base, active):
    items = [
        ("download", "Download", "download/", "nav-download"),
        ("support", "Supported versions", "support/", "nav-support"),
        ("guide", "Guide", "guide/", "nav-guide"),
        ("releases", "Releases", "releases/", "nav-releases"),
    ]
    return "".join(
        internal_link(base, route, label, action, current=(active == key))
        for key, label, route, action in items
    )


def shell(title, description, body, base, canonical_base, active, route=None, state_id=None):
    default_routes = {
        "download": "download/",
        "support": "support/",
        "guide": "guide/",
        "releases": "releases/",
        "accessibility": "accessibility/",
    }
    canonical_route = default_routes.get(active, "") if route is None else route
    canonical = join_url(canonical_base, canonical_route)
    state_id = state_id or active
    brand_current = active == "home"
    accessibility_current = active == "accessibility"
    source = external_link(SOURCE_URL, "Source", "view-source", "source")
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} · VanillaCord</title>
  <meta name="description" content="{html.escape(description, quote=True)}">
  <link rel="canonical" href="{html.escape(canonical, quote=True)}">
  <link rel="describedby" href="{html.escape(join_url(base, 'surface.json'), quote=True)}">
  <link rel="icon" href="{html.escape(join_url(base, 'assets/brand/icon.svg'), quote=True)}" type="image/svg+xml">
  <meta name="color-scheme" content="light dark">
  <meta name="theme-color" content="#F1E2BF">
  <script src="{html.escape(join_url(base, 'assets/site.js'), quote=True)}"></script>
  <link rel="stylesheet" href="{html.escape(join_url(base, 'assets/site.css'), quote=True)}">
</head>
<body>
<a class="skip-link" href="#main-content" data-surface-action="skip-main">Skip to main content</a>
<header class="site-header"><div class="shell"><nav class="site-nav" aria-label="Primary"><a class="brand" href="{html.escape(join_url(base), quote=True)}" data-surface-action="nav-home"{' aria-current="page"' if brand_current else ''}><img class="brand-mark" src="{html.escape(join_url(base, 'assets/brand/icon.svg'), quote=True)}" alt="" aria-hidden="true"><span>VanillaCord</span></a><div class="nav-cluster"><div class="nav-links">{primary_nav(base, active)}</div><label class="theme-control" for="theme-select"><span>Theme</span><select id="theme-select" aria-label="Color theme"><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select></label></div></nav></div></header>
<main id="main-content" class="shell" tabindex="-1" data-surface-state="{html.escape(state_id, quote=True)}">{body}</main>
<footer class="site-footer"><div class="shell footer-row"><span>VanillaCord · SupraCraft · MPL-2.0</span><span>{internal_link(base, 'accessibility/', 'Accessibility', 'nav-accessibility', current=accessibility_current)} · {source}</span></div></footer>
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


def version_slug(version):
    return version.replace(".", "-")


def release_html(release, supported, base, canonical_base):
    artifact = release["artifact"]
    version = release["version"]
    checksum = artifact.get("sha256") or "See release checksums"
    bridge = f'<p><strong>Bridge:</strong> <code>{html.escape(release["bridge_version"])}</code></p>' if release.get("bridge_version") else ""
    table = support_table_html(supported, release.get("minecraft_support", []), f"Minecraft qualification for VanillaCord {version}")
    download = external_link(artifact["download_url"], f'Download {artifact["name"]}', "download-artifact", "artifact-download", "button primary")
    body = f'''<div class="eyebrow">Stable release</div><h1>VanillaCord {html.escape(version)}</h1><p>{html.escape(release.get("summary", "Stable VanillaCord release."))}</p><div class="card"><h2>Download</h2><p>{download}</p><p class="quiet">SHA-256: <code>{html.escape(checksum)}</code></p>{bridge}</div><h2>Supported Minecraft releases</h2><p>Supported means this release patched the Mojang server, produced a readable JAR, and booted it on the listed Java runtime during stable qualification.</p>{table}<div class="card"><h2>Automation</h2><div class="link-list">{resource_link(base, 'releases/stable.json', 'stable.json', 'machine-stable-json')}{resource_link(base, 'releases/stable.txt', 'stable.txt', 'machine-stable-text')}{resource_link(base, 'releases/stable-url.txt', 'stable-url.txt', 'machine-stable-url')}</div></div>'''
    return shell(
        f"Release {version}",
        f"VanillaCord {version} release downloads, checksums, and Minecraft compatibility evidence.",
        body,
        base,
        canonical_base,
        "releases",
        route=f"releases/{version}/",
        state_id=f"release-{version_slug(version)}",
    )


def validate_surface_contract(surface, metadata, stable, manifests):
    expected_base = metadata["homepage"].rstrip("/") + "/"
    if surface.get("production_base_url") != expected_base:
        raise SystemExit(f"PUBLIC_SURFACE.json production_base_url must match homepage: {expected_base}")

    routes = {item["id"]: item for item in surface.get("routes", [])}
    expected_release_routes = {
        f"release-{version_slug(item['version'])}": item["version"]
        for item in manifests
    }
    declared_release_routes = {
        rid: route for rid, route in routes.items() if rid.startswith("release-")
    }
    if set(declared_release_routes) != set(expected_release_routes):
        raise SystemExit(
            "PUBLIC_SURFACE.json release-detail route ids must exactly match release-manifests: "
            f"declared={sorted(declared_release_routes)} expected={sorted(expected_release_routes)}"
        )
    for rid, version in expected_release_routes.items():
        route = routes[rid]
        expected_path = f"/releases/{version}/"
        expected_title = f"Release {version} · VanillaCord"
        if route.get("path") != expected_path or route.get("title") != expected_title:
            raise SystemExit(
                f"PUBLIC_SURFACE.json {rid} must use path {expected_path} and title {expected_title}"
            )

    stable_id = f"release-{version_slug(stable['version'])}"
    if stable_id not in routes:
        raise SystemExit("PUBLIC_SURFACE.json must declare the current stable release-detail route")

    handoffs = {item["action"]: item for item in surface.get("handoffs", [])}
    if handoffs.get("view-source", {}).get("url") != SOURCE_URL:
        raise SystemExit("PUBLIC_SURFACE.json source handoff must match the repository")
    expected_download_prefix = "https://github.com/SupraCraft/VanillaCord/releases/download/"
    if handoffs.get("download-artifact", {}).get("url_prefix") != expected_download_prefix:
        raise SystemExit("PUBLIC_SURFACE.json download-artifact prefix must match release download authority")


def write_sitemap(output, surface):
    urls = []
    for route in surface["routes"]:
        if not route.get("indexable", True):
            continue
        loc = join_url(surface["production_base_url"], route["path"])
        lastmod = route.get("lastmod")
        lastmod_xml = f"<lastmod>{html.escape(lastmod)}</lastmod>" if lastmod else ""
        urls.append(f"  <url><loc>{html.escape(loc)}</loc>{lastmod_xml}</url>")
    write(
        output / "sitemap.xml",
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n",
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
    surface = load(ROOT / "PUBLIC_SURFACE.json")
    canonical_base = metadata["homepage"].rstrip("/")
    base = (args.base_url or canonical_base).rstrip("/")
    manifests = [load(p) for p in sorted((ROOT / "release-manifests").glob("*.json"))] if (ROOT / "release-manifests").is_dir() else []
    if not any(r.get("version") == stable["version"] for r in manifests):
        manifests.append(stable)
    validate_surface_contract(surface, metadata, stable, manifests)

    write_json(output / "project.json", contract)
    write_json(output / "github.json", metadata)
    write_json(output / "brand.json", brand)
    write_json(output / "surface.json", surface)
    write_sitemap(output, surface)
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
            "human_support_matrix": join_url(base, "support/"),
            "machine_support_matrix": join_url(base, "support-matrix.json"),
            "stable_release": stable["version"],
            "note": "This endpoint describes compatibility policy and authoritative support locations; it does not assert that every Minecraft version is supported without release-specific evidence. Release-specific green/red state is published in support-matrix.json and the human support page.",
        },
    )

    artifact = stable["artifact"]
    version = stable["version"]
    checksum = artifact.get("sha256") or "See release checksums"
    download = external_link(artifact["download_url"], f'Download {artifact["name"]}', "download-artifact", "artifact-download", "button primary")
    download_body = f'''<div class="eyebrow">Current stable</div><h1>Download VanillaCord {html.escape(version)}</h1><p>For most server operators, this is the release to use.</p><div class="card"><h2>Stable JAR</h2><div class="actions">{download}{internal_link(base, f'releases/{version}/', 'Release details', 'download-release-detail', 'button')}</div><p class="quiet">SHA-256: <code>{html.escape(checksum)}</code></p></div><h2>Run the patcher</h2><pre><code>java -jar {html.escape(artifact["name"])} &lt;minecraft-version&gt;</code></pre><p>Patched servers are written under <code>out/</code>. Check the {internal_link(base, 'support/', 'supported-version matrix', 'download-support')} for the target runtime, then continue with the {internal_link(base, 'guide/', 'setup guide', 'download-guide')}.</p><div class="notice"><strong>Security:</strong> proxy forwarding changes how backend identity is trusted. Firewall the backend server so players cannot connect around the proxy.</div>'''
    write(output / "download/index.html", shell("Download", f"Download the current stable VanillaCord release {version}, checksum, and release details.", download_body, base, canonical_base, "download"))

    current_target = next((target for target in supported["targets"] if target.get("current")), supported["targets"][0])
    current_mc = html.escape(current_target["version"])
    bash_example = f'''VERSION=$(curl -fsSL {join_url(canonical_base, 'releases/stable.txt')})\nURL=$(curl -fsSL {join_url(canonical_base, 'releases/stable-url.txt')})\ncurl -fL "$URL" -o "vanillacord-$VERSION.jar"'''
    ps_example = f'''$version = (Invoke-RestMethod '{join_url(canonical_base, 'releases/stable.txt')}').Trim()\n$url = (Invoke-RestMethod '{join_url(canonical_base, 'releases/stable-url.txt')}').Trim()\nInvoke-WebRequest $url -OutFile "vanillacord-$version.jar"'''
    guide_body = f'''<div class="eyebrow">End-user guide</div><h1>Set up VanillaCord</h1><h2>1. Check support</h2><p>Start with the {internal_link(base, 'support/', 'supported-version matrix', 'guide-support')}. It records the Java runtime used when each Minecraft generation was qualified.</p><h2>2. Download VanillaCord</h2><p>Get the {internal_link(base, 'download/', 'current stable release', 'guide-download')} and verify its published checksum when your deployment process requires artifact verification.</p><h2>3. Patch your Minecraft release</h2><pre><code>java -jar {html.escape(artifact["name"])} {current_mc}</code></pre><p>Replace <code>{current_mc}</code> with another supported target when needed.</p><h2>4. Run the patched backend</h2><pre><code>java -Xms2G -Xmx2G -jar out/{current_mc}.jar --nogui</code></pre><h2>5. Configure proxy forwarding</h2><p>Choose Velocity, BungeeCord, or BungeeGuard forwarding in <code>vanillacord.txt</code> and use the matching proxy configuration. Keep the backend port firewalled so players cannot bypass the proxy.</p><h2>Automation examples</h2><h3>Bash / Linux</h3><pre><code>{html.escape(bash_example)}</code></pre><h3>PowerShell</h3><pre><code>{html.escape(ps_example)}</code></pre><p>Structured consumers can use {resource_link(base, 'releases/stable.json', 'stable.json', 'machine-stable-json')} and {resource_link(base, 'support-matrix.json', 'support-matrix.json', 'machine-support-matrix')}.</p>'''
    write(output / "guide/index.html", shell("Guide", "Set up VanillaCord, patch a supported Minecraft server, configure proxy forwarding, and automate stable downloads.", guide_body, base, canonical_base, "guide"))

    table = support_table_html(supported, stable.get("minecraft_support", []), f"Supported Minecraft releases for stable VanillaCord {version}")
    support_body = f'''<div class="eyebrow">Compatibility</div><h1>Supported Minecraft releases</h1><p>{html.escape(supported["policy"])}</p><p class="quiet">Current stable VanillaCord: {internal_link(base, f'releases/{version}/', version, 'support-release-stable')}. “Not recorded” means the stable release metadata predates the current structured qualification record; it is not a green support claim.</p>{table}<div class="card"><h2>For automation</h2><p>{resource_link(base, 'support-matrix.json', 'support-matrix.json', 'machine-support-matrix')}</p></div>'''
    write(output / "support/index.html", shell("Supported versions", "Evidence-backed Minecraft and Java runtime compatibility for the current stable VanillaCord release.", support_body, base, canonical_base, "support"))

    links = []
    for release in sorted(manifests, key=lambda r: r["version"], reverse=True):
        release_dir = output / f"releases/{release['version']}"
        write(release_dir / "index.html", release_html(release, supported, base, canonical_base))
        suffix = " — current stable" if release["version"] == version else ""
        action = f"open-release-{version_slug(release['version'])}"
        links.append(f'<li>{internal_link(base, f"releases/{release["version"]}/", f"VanillaCord {release["version"]}", action)}{suffix}</li>')
    releases_body = '<div class="eyebrow">Release history</div><h1>VanillaCord releases</h1><ul>' + "".join(links) + '</ul><p>GitHub remains the developer/source record; normal operator download and information flows stay on this site. Use the secondary Source link in the footer when repository access is actually needed.</p>'
    write(output / "releases/index.html", shell("Releases", "Browse VanillaCord release information and the current stable release.", releases_body, base, canonical_base, "releases"))

    accessibility_body = f'''<div class="eyebrow">Inclusive access</div><h1>Accessibility</h1><p>VanillaCord’s public site targets <strong>WCAG 2.2 Level AA</strong> and is designed to align with Revised Section 508 web accessibility criteria where applicable.</p><h2>Features</h2><ul><li>Semantic page landmarks, a skip-to-content link, structured headings, and accessible table markup.</li><li>Keyboard-visible focus indicators and primary navigation that remains available at narrow and zoomed layouts.</li><li>A Light / Dark / System control. System follows the browser or operating-system color preference; an explicit choice is stored locally in this browser.</li><li>Reduced-motion and forced-colors support using platform preferences.</li><li>External links use a visible ↗ indicator plus an assistive-technology notification and preserve this site in the current browsing context.</li></ul><h2>Testing</h2><p>Pull requests that change the public surface run deterministic route/link checks plus headless browser tests across desktop, 320-pixel reflow, light/dark preference handling, keyboard navigation, and automated WCAG A/AA checks. Automated tools cannot prove full accessibility or Section 508 conformance, so manual review remains part of release readiness for changes that materially alter interaction or content.</p><h2>Report a problem</h2><p>If something on this site is difficult to use with a keyboard, screen reader, zoom, high-contrast mode, or another assistive technology, use the secondary Source link in this page footer to reach the currently available project feedback or contribution channel. Include the affected page, browser/assistive technology if known, and what blocked you.</p>'''
    write(output / "accessibility/index.html", shell("Accessibility", "Accessibility features, testing target, and feedback path for the VanillaCord public site.", accessibility_body, base, canonical_base, "accessibility"))

    write(output / "llms.txt", f'''# VanillaCord\n\nCanonical human entry point: {join_url(canonical_base)}\nDownload: {join_url(canonical_base, 'download/')}\nGuide: {join_url(canonical_base, 'guide/')}\nSupported releases: {join_url(canonical_base, 'support/')}\nAccessibility: {join_url(canonical_base, 'accessibility/')}\nPublic surface contract: {join_url(canonical_base, 'surface.json')}\nSitemap: {join_url(canonical_base, 'sitemap.xml')}\nCurrent stable JSON: {join_url(canonical_base, 'releases/stable.json')}\nCurrent stable version: {join_url(canonical_base, 'releases/stable.txt')}\nCurrent stable artifact URL: {join_url(canonical_base, 'releases/stable-url.txt')}\nSupport matrix JSON: {join_url(canonical_base, 'support-matrix.json')}\nProject contract: {join_url(canonical_base, 'project.json')}\nRepository: https://github.com/{contract['repository']}\nUpstream: https://github.com/{contract['upstream_repository']}\n\nPrefer these endpoints over scraping presentation HTML or GitHub release pages.\n''')


if __name__ == "__main__":
    main()
