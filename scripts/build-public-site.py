#!/usr/bin/env python3
"""Build VanillaCord's end-user and machine-readable GitHub Pages surfaces."""

import argparse, html, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def load(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def write_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(value, encoding="utf-8")


def shell(title, body, base):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} · VanillaCord</title><link rel="icon" href="{base}/assets/brand/icon.svg" type="image/svg+xml"><style>
:root{{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#514A42;background:#F7F2E7;line-height:1.55}}*{{box-sizing:border-box}}body{{margin:0}}a{{color:#7A472D}}.shell{{max-width:980px;margin:auto;padding:0 24px}}header{{background:#F1E2BF;border-bottom:1px solid #D3C39F}}nav{{display:flex;justify-content:space-between;gap:18px;padding:18px 0;flex-wrap:wrap}}nav a{{text-decoration:none;font-weight:650}}main{{padding:42px 0 72px}}h1{{font-size:clamp(2.2rem,6vw,4rem);line-height:1;margin:.2em 0}}h2{{margin-top:2rem}}.eyebrow{{font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;color:#6F6A3D;font-weight:760}}.card{{background:#FFFCF5;border:1px solid #DCD2BF;border-radius:14px;padding:20px;margin:18px 0}}.button{{display:inline-block;border-radius:9px;padding:11px 15px;text-decoration:none;font-weight:700;background:#B86B3F;color:white}}.secondary{{background:#F7F2E7;color:#514A42;border:1px solid #8B785F}}table{{width:100%;border-collapse:collapse;background:#FFFCF5}}th,td{{text-align:left;padding:10px;border-bottom:1px solid #DED5C3}}code{{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;background:#F0E9DB;padding:.1em .3em;border-radius:4px}}pre{{overflow:auto;background:#2E2B28;color:#FAF6ED;padding:16px;border-radius:10px}}.dot{{display:inline-block;width:.72em;height:.72em;border-radius:50%;margin-right:.45em}}.green{{background:#278451}}.red{{background:#C33E3E}}.gray{{background:#8A8379}}.quiet{{color:#716A61}}footer{{border-top:1px solid #DCD2BF;padding:24px 0 40px;color:#716A61}}</style></head><body><header><div class="shell"><nav><a href="{base}/">VanillaCord</a><span><a href="{base}/download/">Download</a> · <a href="{base}/support/">Support</a> · <a href="{base}/guide/">Guide</a> · <a href="{base}/releases/">Releases</a></span></nav></div></header><main class="shell">{body}</main><footer><div class="shell">VanillaCord · SupraCraft · MPL-2.0</div></footer></body></html>'''


def state(status):
    return {'pass':'<span class="dot green"></span>Supported','fail':'<span class="dot red"></span>Failed qualification'}.get(status,'<span class="dot gray"></span>Not recorded for this release')


def support_table(supported, evidence):
    found = {item.get('version'): item for item in evidence or []}
    rows = []
    for target in supported['targets']:
        result = found.get(target['version'], {})
        rows.append(f"<tr><td>{state(result.get('status'))}</td><td><code>{html.escape(target['version'])}</code></td><td>{html.escape(target['generation'])}</td><td>Java {int(target['java'])}</td></tr>")
    return ''.join(rows)


def release_html(release, supported, base):
    artifact = release['artifact']; version = release['version']; checksum = artifact.get('sha256') or 'See release checksums'
    bridge = f"<p><strong>Bridge:</strong> <code>{html.escape(release['bridge_version'])}</code></p>" if release.get('bridge_version') else ''
    table = support_table(supported, release.get('minecraft_support', []))
    return shell(f"Release {version}", f'''<div class="eyebrow">Stable release</div><h1>VanillaCord {html.escape(version)}</h1><p>{html.escape(release.get('summary','Stable VanillaCord release.'))}</p><div class="card"><h2>Download</h2><p><a class="button" href="{html.escape(artifact['download_url'])}">Download {html.escape(artifact['name'])}</a></p><p class="quiet">SHA-256: <code>{html.escape(checksum)}</code></p>{bridge}</div><h2>Supported Minecraft releases</h2><p>Green means this release patched the Mojang server, produced a readable JAR, and booted it on the listed Java runtime during stable qualification.</p><table><thead><tr><th>State</th><th>Minecraft</th><th>Generation</th><th>Runtime</th></tr></thead><tbody>{table}</tbody></table><div class="card"><h2>Automation</h2><p><a href="{base}/releases/stable.json">stable.json</a> · <a href="{base}/releases/stable.txt">stable.txt</a> · <a href="{base}/releases/stable-url.txt">stable-url.txt</a></p></div>''', base)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output', default='build/public-site'); args = parser.parse_args()
    output = (ROOT / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output)
    if output.exists(): shutil.rmtree(output)
    shutil.copytree(DOCS, output)

    contract = load(ROOT/'PROJECT_CONTRACT.json'); metadata = load(ROOT/'GITHUB_METADATA.json'); brand = load(DOCS/'assets/brand/brand.json')
    stable = load(ROOT/'STABLE_RELEASE.json'); supported = load(ROOT/'SUPPORTED_MINECRAFT.json'); base = metadata['homepage'].rstrip('/')
    manifests = [load(p) for p in sorted((ROOT/'release-manifests').glob('*.json'))] if (ROOT/'release-manifests').is_dir() else []
    if not any(r.get('version') == stable['version'] for r in manifests): manifests.append(stable)

    write_json(output/'project.json', contract); write_json(output/'github.json', metadata); write_json(output/'brand.json', brand)
    write_json(output/'releases/stable.json', stable); write(output/'releases/stable.txt', stable['version']+'\n'); write(output/'releases/stable-url.txt', stable['artifact']['download_url']+'\n'); write(output/'releases/stable-sha256.txt', (stable['artifact'].get('sha256') or '')+'\n')
    support_endpoint = {'schema':'vanillacord-public-support-matrix/1','stable_release':stable['version'],'policy':supported['policy'],'selection':supported['selection'],'targets':supported['targets'],'results':stable.get('minecraft_support',[])}
    write_json(output/'support-matrix.json', support_endpoint)
    write_json(output/'artifacts.json', {'schema_version':'1.1.0','repository':contract['repository'],'source_version':contract['source_version'],'stable_release':stable,'artifact':contract['artifact'],'versioning':contract['versioning'],'provenance':contract['provenance']})
    write_json(output/'compatibility.json', {'schema_version':'1.1.0','repository':contract['repository'],'tiers':contract['validation']['compatibility_tiers'],'human_support_matrix':base+'/support/','machine_support_matrix':base+'/support-matrix.json','stable_release':stable['version'],'note':'This endpoint describes compatibility policy and authoritative support locations; it does not assert that every Minecraft version is supported without release-specific evidence. Release-specific green/red state is published in support-matrix.json and the human support page.'})

    artifact = stable['artifact']; version = stable['version']; checksum = artifact.get('sha256') or 'See release checksums'
    write(output/'download/index.html', shell('Download', f'''<div class="eyebrow">Current stable</div><h1>Download VanillaCord {html.escape(version)}</h1><p>For most users, this is the release to use.</p><div class="card"><p><a class="button" href="{html.escape(artifact['download_url'])}">Download {html.escape(artifact['name'])}</a> <a class="button secondary" href="{base}/releases/{html.escape(version)}/">Release details</a></p><p class="quiet">SHA-256: <code>{html.escape(checksum)}</code></p></div><h2>Run it</h2><pre>java -jar {html.escape(artifact['name'])} &lt;minecraft-version&gt;</pre><p>Patched servers are written under <code>out/</code>. Continue with the <a href="{base}/guide/">setup guide</a>.</p>''', base))
    bash_example = f'''VERSION=$(curl -fsSL {base}/releases/stable.txt)\nURL=$(curl -fsSL {base}/releases/stable-url.txt)\ncurl -fL "$URL" -o "vanillacord-$VERSION.jar"'''
    ps_example = f'''$version = (Invoke-RestMethod '{base}/releases/stable.txt').Trim()\n$url = (Invoke-RestMethod '{base}/releases/stable-url.txt').Trim()\nInvoke-WebRequest $url -OutFile "vanillacord-$version.jar"'''
    write(output/'guide/index.html', shell('Guide', f'''<div class="eyebrow">End-user guide</div><h1>Set up VanillaCord</h1><h2>1. Download</h2><p>Get the <a href="{base}/download/">current stable release</a>.</p><h2>2. Patch your Minecraft release</h2><pre>java -jar {html.escape(artifact['name'])} 26.2</pre><h2>3. Run the patched backend</h2><pre>java -Xms2G -Xmx2G -jar out/26.2.jar --nogui</pre><h2>4. Configure forwarding</h2><p>Choose Velocity, BungeeCord, or BungeeGuard forwarding in <code>vanillacord.txt</code>, use the matching proxy configuration, and firewall the backend port so players cannot bypass the proxy.</p><p>Check the <a href="{base}/support/">support matrix</a> before selecting a Minecraft version.</p><h2>Automation examples</h2><p>Bash / Linux:</p><pre>{html.escape(bash_example)}</pre><p>PowerShell:</p><pre>{html.escape(ps_example)}</pre><p>For structured consumers, use <a href="{base}/releases/stable.json">stable.json</a> and <a href="{base}/support-matrix.json">support-matrix.json</a>.</p>''', base))
    table = support_table(supported, stable.get('minecraft_support', []))
    write(output/'support/index.html', shell('Support', f'''<div class="eyebrow">Compatibility</div><h1>Supported Minecraft releases</h1><p>{html.escape(supported['policy'])}</p><p class="quiet">Current stable VanillaCord: <a href="{base}/releases/{html.escape(version)}/">{html.escape(version)}</a>. Gray means older release metadata did not record the current structured qualification.</p><table><thead><tr><th>State</th><th>Minecraft</th><th>Generation</th><th>Runtime</th></tr></thead><tbody>{table}</tbody></table><div class="card"><h2>For automation</h2><p><a href="{base}/support-matrix.json">support-matrix.json</a></p></div>''', base))

    links=[]
    for release in sorted(manifests, key=lambda r:r['version'], reverse=True):
        write(output/f"releases/{release['version']}/index.html", release_html(release, supported, base)); links.append(f'''<li><a href="{base}/releases/{html.escape(release['version'])}/">VanillaCord {html.escape(release['version'])}</a>{' — current stable' if release['version']==version else ''}</li>''')
    write(output/'releases/index.html', shell('Releases', '<div class="eyebrow">Release history</div><h1>VanillaCord releases</h1><ul>'+''.join(links)+'</ul><p>GitHub remains the developer/source record; normal operator download and information flows stay on this site.</p>', base))
    write(output/'llms.txt', f'''# VanillaCord\n\nCanonical human entry point: {base}/\nDownload: {base}/download/\nGuide: {base}/guide/\nSupported releases: {base}/support/\nCurrent stable JSON: {base}/releases/stable.json\nCurrent stable version: {base}/releases/stable.txt\nCurrent stable artifact URL: {base}/releases/stable-url.txt\nSupport matrix JSON: {base}/support-matrix.json\nProject contract: {base}/project.json\nRepository: https://github.com/{contract['repository']}\nUpstream: https://github.com/{contract['upstream_repository']}\n\nPrefer these endpoints over scraping presentation HTML or GitHub release pages.\n''')

if __name__ == '__main__': main()
