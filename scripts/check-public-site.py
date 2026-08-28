#!/usr/bin/env python3
"""Validate a generated or deployed SupraCraft public site against repository contracts."""

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class SiteReader:
    def __init__(self, site_dir=None, base_url=None):
        self.site_dir = Path(site_dir).resolve() if site_dir else None
        self.base_url = base_url.rstrip("/") if base_url else None

    def read_text(self, relative_path: str) -> str:
        if self.site_dir is not None:
            path = self.site_dir / relative_path
            if not path.is_file():
                raise AssertionError(f"missing public-site file: {relative_path}")
            return path.read_text(encoding="utf-8")

        url = f"{self.base_url}/{relative_path.lstrip('/')}"
        error = None
        for attempt in range(10):
            try:
                request = urllib.request.Request(
                    url,
                    headers={"User-Agent": "SupraCraft-public-surface-check/1"},
                )
                with urllib.request.urlopen(request, timeout=20) as response:
                    if response.status != 200:
                        raise AssertionError(f"{url}: HTTP {response.status}")
                    return response.read().decode("utf-8")
            except (OSError, UnicodeError, urllib.error.HTTPError, urllib.error.URLError) as exc:
                error = exc
                if attempt == 9:
                    break
                time.sleep(3)
        raise AssertionError(f"unable to read {url}: {error}")


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--site-dir")
    mode.add_argument("--base-url")
    args = parser.parse_args()

    contract = load_json(ROOT / "PROJECT_CONTRACT.json")
    metadata = load_json(ROOT / "GITHUB_METADATA.json")
    expected_brand = load_json(ROOT / "docs/assets/brand/brand.json")
    reader = SiteReader(site_dir=args.site_dir, base_url=args.base_url)

    page = reader.read_text("index.html")
    assert '<html lang="en">' in page
    assert '<meta name="viewport"' in page
    assert f'<link rel="canonical" href="{metadata["homepage"]}">' in page
    assert metadata["description"] in page
    assert contract["upstream_repository"] in page
    assert 'href="assets/brand/icon.svg"' in page

    for asset in ("assets/brand/icon.svg", "assets/brand/hero.svg"):
        assert reader.read_text(asset).strip(), f"empty public-site asset: {asset}"

    endpoints = contract["public_surface"]["machine_endpoints"]
    for name in endpoints:
        assert f'href="{name}"' in page, f"index.html does not link machine endpoint: {name}"
        assert reader.read_text(name).strip(), f"empty machine endpoint: {name}"

    project = json.loads(reader.read_text("project.json"))
    github = json.loads(reader.read_text("github.json"))
    brand = json.loads(reader.read_text("brand.json"))
    artifacts = json.loads(reader.read_text("artifacts.json"))

    assert project == contract
    assert github == metadata
    assert brand == expected_brand
    assert artifacts["repository"] == contract["repository"]
    assert artifacts["source_version"] == contract["source_version"]
    assert artifacts["artifact"] == contract["artifact"]
    assert artifacts["versioning"] == contract["versioning"]
    assert artifacts["provenance"] == contract["provenance"]

    if "compatibility.json" in endpoints:
        compatibility = json.loads(reader.read_text("compatibility.json"))
        assert compatibility["repository"] == contract["repository"]
        assert compatibility["tiers"] == contract["validation"]["compatibility_tiers"]

    llms = reader.read_text("llms.txt")
    base = metadata["homepage"].rstrip("/")
    assert f"Canonical human entry point: {base}/" in llms
    assert f"Repository: https://github.com/{contract['repository']}" in llms
    assert f"Upstream: https://github.com/{contract['upstream_repository']}" in llms

    if 'id="source-version"' in page:
        assert (
            f'id="source-version">{contract["source_version"]}</code>' in page
        ), "rendered source-version does not match PROJECT_CONTRACT.json"

    if 'id="java-release"' in page:
        assert (
            f'id="java-release">{contract["toolchain"]["java_bytecode_release"]}</span>' in page
        ), "rendered Java release does not match PROJECT_CONTRACT.json"

    source = args.site_dir if args.site_dir else args.base_url
    print(f"Public-site contract OK: {source}")


if __name__ == "__main__":
    main()
