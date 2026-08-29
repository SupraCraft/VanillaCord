#!/usr/bin/env python3
"""Validate generated or deployed VanillaCord Pages surfaces."""

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTE_ATTEMPTS = 30
REMOTE_DELAY_SECONDS = 5


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class SiteReader:
    def __init__(self, site_dir=None, base_url=None):
        self.site_dir = Path(site_dir).resolve() if site_dir else None
        self.base_url = base_url.rstrip("/") if base_url else None
        self.cache_key = None

    def begin_attempt(self, attempt: int):
        if self.base_url is not None:
            self.cache_key = f"{int(time.time())}-{attempt}"

    def read_text(self, relative_path: str) -> str:
        if self.site_dir is not None:
            path = self.site_dir / relative_path
            if not path.is_file():
                raise AssertionError(f"missing public-site file: {relative_path}")
            return path.read_text(encoding="utf-8")
        url = f"{self.base_url}/{relative_path.lstrip('/')}"
        if self.cache_key:
            url = f"{url}?{urllib.parse.urlencode({'supra_check': self.cache_key})}"
        request = urllib.request.Request(url, headers={"User-Agent": "SupraCraft-public-surface-check/2", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status != 200:
                raise AssertionError(f"{url}: HTTP {response.status}")
            return response.read().decode("utf-8")


def validate_site(reader, contract, metadata, expected_brand, stable, supported):
    page = reader.read_text("index.html")
    assert '<html lang="en">' in page
    assert '<meta name="viewport"' in page
    assert f'<link rel="canonical" href="{metadata["homepage"]}">' in page
    assert metadata["description"] in page
    assert contract["upstream_repository"] in page
    assert 'href="assets/brand/icon.svg"' in page
    assert 'href="download/"' in page
    assert 'href="support/"' in page
    assert 'href="guide/"' in page
    assert 'href="releases/"' in page

    for asset in ("assets/brand/icon.svg", "assets/brand/hero.svg"):
        assert reader.read_text(asset).strip(), f"empty public-site asset: {asset}"

    for name in contract["public_surface"]["machine_endpoints"]:
        assert f'href="{name}"' in page, f"index.html does not link machine endpoint: {name}"
        assert reader.read_text(name).strip(), f"empty machine endpoint: {name}"

    project = json.loads(reader.read_text("project.json"))
    github = json.loads(reader.read_text("github.json"))
    brand = json.loads(reader.read_text("brand.json"))
    artifacts = json.loads(reader.read_text("artifacts.json"))
    compatibility = json.loads(reader.read_text("compatibility.json"))
    stable_endpoint = json.loads(reader.read_text("releases/stable.json"))
    support_endpoint = json.loads(reader.read_text("support-matrix.json"))

    assert project == contract
    assert github == metadata
    assert brand == expected_brand
    assert artifacts["repository"] == contract["repository"]
    assert artifacts["stable_release"] == stable
    assert compatibility["tiers"] == contract["validation"]["compatibility_tiers"]
    assert stable_endpoint == stable
    assert reader.read_text("releases/stable.txt").strip() == stable["version"]
    assert reader.read_text("releases/stable-url.txt").strip() == stable["artifact"]["download_url"]
    assert reader.read_text("releases/stable-sha256.txt").strip() == (stable["artifact"].get("sha256") or "")
    assert support_endpoint["stable_release"] == stable["version"]
    assert support_endpoint["targets"] == supported["targets"]
    assert support_endpoint["results"] == stable.get("minecraft_support", [])

    download = reader.read_text("download/index.html")
    guide = reader.read_text("guide/index.html")
    support = reader.read_text("support/index.html")
    releases = reader.read_text("releases/index.html")
    release = reader.read_text(f"releases/{stable['version']}/index.html")
    for rendered in (download, release):
        assert stable["version"] in rendered
        assert stable["artifact"]["download_url"] in rendered
    assert "Set up VanillaCord" in guide
    assert "Supported Minecraft releases" in support
    assert "State" in support and "Minecraft" in support and "Runtime" in support
    for target in supported["targets"]:
        assert target["version"] in support
    assert stable["version"] in releases

    llms = reader.read_text("llms.txt")
    base = metadata["homepage"].rstrip("/")
    assert f"Canonical human entry point: {base}/" in llms
    assert f"Current stable JSON: {base}/releases/stable.json" in llms
    assert f"Current stable artifact URL: {base}/releases/stable-url.txt" in llms
    assert f"Repository: https://github.com/{contract['repository']}" in llms
    assert f"Upstream: https://github.com/{contract['upstream_repository']}" in llms


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--site-dir")
    mode.add_argument("--base-url")
    args = parser.parse_args()

    contract = load_json(ROOT / "PROJECT_CONTRACT.json")
    metadata = load_json(ROOT / "GITHUB_METADATA.json")
    expected_brand = load_json(ROOT / "docs/assets/brand/brand.json")
    stable = load_json(ROOT / "STABLE_RELEASE.json")
    supported = load_json(ROOT / "SUPPORTED_MINECRAFT.json")
    reader = SiteReader(site_dir=args.site_dir, base_url=args.base_url)

    if args.site_dir:
        validate_site(reader, contract, metadata, expected_brand, stable, supported)
    else:
        retryable = (AssertionError, json.JSONDecodeError, OSError, UnicodeError, urllib.error.HTTPError, urllib.error.URLError)
        last_error = None
        for attempt in range(1, REMOTE_ATTEMPTS + 1):
            reader.begin_attempt(attempt)
            try:
                validate_site(reader, contract, metadata, expected_brand, stable, supported)
                break
            except retryable as exc:
                last_error = exc
                if attempt == REMOTE_ATTEMPTS:
                    raise AssertionError(f"deployed public-site contract did not converge after {REMOTE_ATTEMPTS} attempts: {exc}") from exc
                print(f"Public site not converged (attempt {attempt}/{REMOTE_ATTEMPTS}): {exc}", flush=True)
                time.sleep(REMOTE_DELAY_SECONDS)
        else:
            raise AssertionError(f"deployed public-site contract did not converge: {last_error}")

    source = args.site_dir if args.site_dir else args.base_url
    print(f"Public-site contract OK: {source}")


if __name__ == "__main__":
    main()
