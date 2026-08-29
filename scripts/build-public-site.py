#!/usr/bin/env python3
"""Build the VanillaCord GitHub Pages artifact from repository source-of-truth files."""

import argparse
import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def shell(title: str, body: str, base: str):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · VanillaCord</title><link rel="icon" href="{base}/assets/brand/icon.svg" type="image/svg+xml">
<style>
:root{{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#514A42;background:#F7F2E7;line-height:1.55}}*{{box-sizing:border-box}}body{{margin:0}}a{{color:#7A472D}}.shell{{max-width:980px;margin:auto;padding:0 24px}}header{{background:#F1E2BF;border-bottom:1px solid #D3C39F}}nav{{display:flex;justify-content:space-between;align-items:center;gap:18px;padding:18px 0;flex-wrap:wrap}}nav a{{text-decoration:none;font-weight:650}}main{{padding:42px 0 72px}}h1{{font-size:clamp(2.2rem,6vw,4rem);line-height:1;margin:.2em 0}}h2{{margin-top:2rem}}.eyebrow{{font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;color:#6F6A3D;font-weight:760}}.card{{background:#FFFCF5;border:1px solid #DCD2BF;border-radius:14px;padding:20px;margin:18px 0}}.button{{display:inline-block;border-radius:9px;padding:11px 15px;text-decoration:none;font-weight:700;background:#B86B3F;color:white}}.secondary{{background:#F7F2E7;color:#514A42;border:1px solid #8B785F}}table{{width:100%;border-collapse:collapse;background:#FFFCF5}}th,td{{text-align:left;padding:10px;border-bottom:1px solid #DED5C3}}code{{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;background:#F0E9DB;padding:.1em .3em;border-radius:4px}}pre{{overflow:auto;background:#2E2B28;color:#FAF6ED;padding:16px;border-radius:10px}}.dot{{display:inline-block;width:.72em;height:.72em;border-radius:50%;margin-right:.45em;vertical-align:.02em}}.green{{background:#278451}}.red{{background:#C33E3E}}.gray{{background:#8A8379}}.quiet{{color:#716A61}}footer{{border-top:1px solid #DCD2BF;padding:24px 0 40px;color:#716A61}}
</style></head><body><header><div class="shell"><nav><a href="{base}/">VanillaCord</a><span><a href="{base}/download/">Download</a> · <a href="{base}/support/">Support</a> · <a href="{base}/guide/">Guide</a> · <a href="{base}/releases/">Releases</a></span></nav></div></header><main class="shell">{body}</main><footer><div class="shell">VanillaCord · SupraCraft · MPL-2.0</div></footer></body></html>"""


def status_cell(status: str):
    if status == "pass":
        return '<span class="dot green"></span>Supported'
    if status == "fail":
        return '<span class="dot red"></span>Failed qualification'
    return '<span class="dot gray"></span>Not recorded for this release'


def support_rows(support, evidence):
    evidence_by_version = {item.get("version"): item for item in evidence or []}
    rows = []
    for target in support["targets"]:
        result = evidence_by_version.get(target["version"], {})
        rows.append(
            "<tr>"
            f"<td>{status_cell(result.get('status', 'unknown'))}</td>"
            f"<td><code>{html.escape(target['version'])}</code></td>"
            f"<td>{html.escape(target['generation'])}</td>"
            f"<td>Java {int(target['java'])}</td>"
            "</tr>"
        )
    return "".join(rows)


def release_page(release, support, base):
    version = release["version"]
    artifact = release["artifact"]
    evidence = release.get("minecraft_support", [])
    table = support_rows(support, evidence)
    checksum = artifact.get("sha256") or "See release checksums"
    bridge = release.get("bridge_version")
    bridge_html = f"<p><strong>Bridge:</strong> <code>{html.escape(bridge)}</code></p>" if bridge else ""
    body = f"""
<div class="eyebrow">Stable release</div><h1>VanillaCord {html.escape(version)}</h1>
<p>{html.escape(release.get('summary', 'Stable VanillaCord release.'))}</p>
<div class="card"><h2>Download</h2><p><a class="button" href="{html.escape(artifact['download_url'])}">Download {html.escape(artifact['name'])}</a></p><p class="quiet">SHA-256: <code>{html.escape(checksum)}</code></p>{bridge_html}</div>
<h2>Supported Minecraft releases</h2><p>A green row means this VanillaCord release patched that Mojang server, produced a readable server JAR, and booted it on the listed Java runtime during the blocking stable-release qualification.</p>
<table><thead><tr><th>State</th><th>Minecraft</th><th>Generation</th><th>Runtime</th></tr></thead><tbody>{table}</tbody></table>
<div class="card"><h2>Automation</h2><p>For scripts that always need the current stable build, use <a href="{base}/releases/stable.json">stable.json</a>, <a href="{base}/releases/stable.txt">stable.txt</a>, or <a href="{base}/releases/stable-url.txt">stable-url.txt</a>.</p></div>
"""
    return shell(f"Release {version}", body, base)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="build/public-site")
    args = parser.parse_args()

    output = (ROOT / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output)
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(DOCS, output)

    contract = load_json(ROOT / "PROJECT_CONTRACT.json")
    metadata = load_json(ROOT / "GITHUB_METADATA.json")
    brand = load_json(DOCS / "assets/brand/brand.json")
    stable = load_json(ROOT / "STABLE_RELEASE.json")
    support = load_json(ROOT / "SUPPORTED_MINECRAFT.json")
    base = metadata["homepage"].rstrip("/")

    manifests = []
    manifest_dir = ROOT / "release-manifests"
    if manifest_dir.is_dir():
        for path in sorted(manifest_dir.glob("*.json")):
            manifests.append(load_json(path))
    if not any(item.get("version") == stable.get("version") for item in manifests):
        manifests.append(stable)

    write_json(output / "project.json", contract)
    write_json(output / "github.json", metadata)
    write_json(output / "brand.json", brand)
    write_json(output / "releases/stable.json", stable)
    write_text(output / "releases/stable.txt", stable["version"] + "\n")
    write_text(output / "releases/stable-url.txt", stable["artifact"]["download_url"] + "\n")
    write_text(output / "releases/stable-sha256.txt", (stable["artifact"].get("sha256") or "") + "\n")

    support_endpoint = {
        "schema": "vanillacord-public-support-matrix/1",
        "stable_release": stable["version"],
        "policy": support["policy"],
        "selection": support["selection"],
        "targets": support["targets"],
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
            "human_support_matrix": f"{base}/support/",
            "machine_support_matrix": f"{base}/support-matrix.json",
            "stable_release": stable["version"],
        },
    )

    download_body = f"""<div class="eyebrow">Current stable</div><h1>Download VanillaCord {html.escape(stable['version'])}</h1><p>For most users, this is the release to use.</p><div class="card"><p><a class="button" href="{html.escape(stable['artifact']['download_url'])}">Download {html.escape(stable['artifact']['name'])}</a> <a class="button secondary" href="{base}/releases/{html.escape(stable['version'])}/">Release details</a></p><p class="quiet">SHA-256: <code>{html.escape(stable['artifact'].get('sha256') or 'See release checksums')}</code></p></div><h2>Run it</h2><pre>java -jar {html.escape(stable['artifact']['name'])} &lt;minecraft-version&gt;</pre><p>The patched server will be written under <code>out/</code>. See the <a href="{base}/guide/">setup guide</a> for proxy and backend configuration.</p>"""
    write_text(output / "download/index.html", shell("Download", download_body, base))

    guide_body = f"""<div class="eyebrow">End-user guide</div><h1>Set up VanillaCord</h1><h2>1. Download</h2><p>Get the <a href="{base}/download/">current stable VanillaCord release</a>.</p><h2>2. Patch the server version you use</h2><pre>java -jar {html.escape(stable['artifact']['name'])} 26.2</pre><h2>3. Run the patched backend</h2><pre>java -Xms2G -Xmx2G -jar out/26.2.jar --nogui</pre><h2>4. Configure forwarding</h2><p>Choose Velocity, BungeeCord, or BungeeGuard forwarding in <code>vanillacord.txt</code> and use the matching proxy configuration. Keep the backend server port firewalled so players cannot bypass the proxy.</p><p>Before selecting a Minecraft release, check the <a href="{base}/support/">support matrix</a>.</p>"""
    write_text(output / "guide/index.html", shell("Guide", guide_body, base))

    support_table = support_rows(support, stable.get("minecraft_support", []))
    support_body = f"""<div class="eyebrow">Compatibility</div><h1>Supported Minecraft releases</h1><p>{html.escape(support['policy'])}</p><p class="quiet">Current stable VanillaCord: <a href="{base}/releases/{html.escape(stable['version'])}/">{html.escape(stable['version'])}</a>. Status below is release-specific evidence; gray means older release metadata did not record the current structured qualification.</p><table><thead><tr><th>State</th><th>Minecraft</th><th>Generation</th><th>Runtime</th></tr></thead><tbody>{support_table}</tbody></table><div class="card"><h2>For automation</h2><p><a href="{base}/support-matrix.json">support-matrix.json</a> exposes this table as structured data.</p></div>"""
    write_text(output / "support/index.html", shell("Support", support_body, base))

    release_links = []
    for release in sorted(manifests, key=lambda item: item["version"], reverse=True):
        version = release["version"]
        write_text(output / f"releases/{version}/index.html", release_page(release, support, base))
        release_links.append(f'<li><a href="{base}/releases/{html.escape(version)}/">VanillaCord {html.escape(version)}</a>{" — current stable" if version == stable["version"] else ""}</li>')
    releases_body = f"<div class=\"eyebrow\">Release history</div><h1>VanillaCord releases</h1><ul>{''.join(release_links)}</ul><p>Developer-oriented GitHub release records remain available from the source repository, but normal download and documentation flows stay on this site.</p>"
    write_text(output / "releases/index.html", shell("Releases", releases_body, base))

    llms = f"""# VanillaCord\n\nCanonical human entry point: {base}/\nDownload: {base}/download/\nGuide: {base}/guide/\nSupported releases: {base}/support/\nCurrent stable JSON: {base}/releases/stable.json\nCurrent stable version: {base}/releases/stable.txt\nCurrent stable artifact URL: {base}/releases/stable-url.txt\nSupport matrix JSON: {base}/support-matrix.json\nProject contract: {base}/project.json\nRepository: https://github.com/{contract['repository']}\nUpstream: https://github.com/{contract['upstream_repository']}\n\nPrefer these stable endpoints over scraping presentation HTML or GitHub release pages.\n"""
    write_text(output / "llms.txt", llms)


if __name__ == "__main__":
    main()
