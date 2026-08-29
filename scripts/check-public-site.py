#!/usr/bin/env python3
"""Validate generated or deployed VanillaCord Pages surfaces."""

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
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
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "SupraCraft-public-surface-check/4",
                "Cache-Control": "no-cache",
            },
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status != 200:
                raise AssertionError(f"{url}: HTTP {response.status}")
            return response.read().decode("utf-8")


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.fragments = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])
        for attr in ("href", "src"):
            value = values.get(attr)
            if value:
                self.links.append(value)
        href = values.get("href")
        if href and href.startswith("#") and href != "#":
            self.fragments.append(href[1:])


def expected_file_for_url(url, base):
    parsed = urllib.parse.urlparse(url)
    base_parsed = urllib.parse.urlparse(base.rstrip("/") + "/")
    if parsed.scheme not in ("", "http", "https"):
        return None
    if parsed.netloc and (parsed.scheme, parsed.netloc) != (
        base_parsed.scheme,
        base_parsed.netloc,
    ):
        return None
    path = parsed.path
    base_path = base_parsed.path.rstrip("/") + "/"
    if path.startswith(base_path):
        relative = path[len(base_path) :]
    elif not parsed.netloc:
        relative = path.lstrip("/")
    else:
        return None
    relative = urllib.parse.unquote(relative)
    if not relative or relative.endswith("/"):
        relative += "index.html"
    return relative


def validate_internal_links(site_dir: Path, base: str):
    site_dir = site_dir.resolve()
    for html_path in sorted(site_dir.rglob("*.html")):
        relative_page = html_path.relative_to(site_dir).as_posix()
        public_url = urllib.parse.urljoin(base.rstrip("/") + "/", relative_page)
        parser = LinkCollector()
        parser.feed(html_path.read_text(encoding="utf-8"))
        for fragment in parser.fragments:
            assert (
                urllib.parse.unquote(fragment) in parser.ids
            ), f"{relative_page}: broken fragment #{fragment}"
        for raw in parser.links:
            if raw.startswith(("mailto:", "tel:", "javascript:", "data:")):
                continue
            resolved = urllib.parse.urljoin(public_url, raw)
            target = expected_file_for_url(resolved, base)
            if target is None:
                continue
            target_path = (site_dir / target).resolve()
            assert (
                target_path == site_dir or site_dir in target_path.parents
            ), f"{relative_page}: internal link escapes site root: {raw}"
            assert (
                target_path.is_file()
            ), f"{relative_page}: broken internal link/resource {raw} -> {target}"


def assert_common_page(page: str, label: str):
    for fragment in (
        '<html lang="en">',
        '<meta name="viewport"',
        '<meta name="description"',
        '<meta name="color-scheme" content="light dark">',
        'class="skip-link" href="#main-content"',
        'aria-label="Primary"',
        'class="brand-mark"',
        'id="theme-select"',
        '<main id="main-content"',
        'tabindex="-1"',
        '>Accessibility</a>',
    ):
        assert fragment in page, f"{label}: missing common user-surface element: {fragment}"
    assert (
        page.count('aria-current="page"') == 1
    ), f"{label}: expected exactly one aria-current=page marker"


def validate_site(
    reader,
    contract,
    metadata,
    expected_brand,
    stable,
    supported,
    navigation_base,
):
    navigation_base = navigation_base.rstrip("/")
    page = reader.read_text("index.html")
    assert_common_page(page, "index.html")
    assert f'<link rel="canonical" href="{metadata["homepage"]}">' in page
    assert metadata["description"] in page
    assert contract["upstream_repository"] in page
    assert 'href="assets/brand/icon.svg"' in page
    assert 'href="download/"' in page
    assert 'href="support/"' in page
    assert 'href="guide/"' in page
    assert 'href="releases/"' in page
    assert 'href="accessibility/"' in page

    for asset in (
        "assets/brand/icon.svg",
        "assets/brand/hero.svg",
        "assets/site.css",
        "assets/site.js",
    ):
        assert reader.read_text(asset).strip(), f"empty public-site asset: {asset}"

    css = reader.read_text("assets/site.css")
    js = reader.read_text("assets/site.js")
    assert "prefers-color-scheme: dark" in css
    assert "prefers-reduced-motion: reduce" in css
    assert "forced-colors: active" in css
    assert ".skip-link" in css and ":focus-visible" in css
    assert "display:none" not in css.replace(
        " ", ""
    ), "site.css must not hide primary navigation at narrow widths"
    assert "supracraft-theme" in js
    assert "prefers-color-scheme: dark" in js
    assert "localStorage" in js

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
    assert compatibility["human_support_matrix"] == navigation_base + "/support/"
    assert compatibility["machine_support_matrix"] == navigation_base + "/support-matrix.json"
    assert stable_endpoint == stable
    assert reader.read_text("releases/stable.txt").strip() == stable["version"]
    assert (
        reader.read_text("releases/stable-url.txt").strip()
        == stable["artifact"]["download_url"]
    )
    assert reader.read_text("releases/stable-sha256.txt").strip() == (
        stable["artifact"].get("sha256") or ""
    )
    assert support_endpoint["stable_release"] == stable["version"]
    assert support_endpoint["targets"] == supported["targets"]
    assert support_endpoint["results"] == stable.get("minecraft_support", [])

    pages = {
        "download/index.html": reader.read_text("download/index.html"),
        "guide/index.html": reader.read_text("guide/index.html"),
        "support/index.html": reader.read_text("support/index.html"),
        "releases/index.html": reader.read_text("releases/index.html"),
        f"releases/{stable['version']}/index.html": reader.read_text(
            f"releases/{stable['version']}/index.html"
        ),
        "accessibility/index.html": reader.read_text("accessibility/index.html"),
    }
    for name, rendered in pages.items():
        assert_common_page(rendered, name)
        assert f"{navigation_base}/assets/site.css" in rendered
        assert f"{navigation_base}/assets/site.js" in rendered
        assert f"{navigation_base}/assets/brand/icon.svg" in rendered

    download = pages["download/index.html"]
    guide = pages["guide/index.html"]
    support = pages["support/index.html"]
    releases = pages["releases/index.html"]
    release = pages[f"releases/{stable['version']}/index.html"]
    accessibility = pages["accessibility/index.html"]
    for rendered in (download, release):
        assert stable["version"] in rendered
        assert stable["artifact"]["download_url"] in rendered
    assert "Set up VanillaCord" in guide
    assert "Supported Minecraft releases" in support
    assert 'scope="col"' in support and "<caption>" in support
    for target in supported["targets"]:
        assert target["version"] in support
    assert stable["version"] in releases
    assert "WCAG 2.2 Level AA" in accessibility
    assert "automated" in accessibility.lower() and "manual" in accessibility.lower()

    llms = reader.read_text("llms.txt")
    assert f"Canonical human entry point: {navigation_base}/" in llms
    assert f"Accessibility: {navigation_base}/accessibility/" in llms
    assert f"Current stable JSON: {navigation_base}/releases/stable.json" in llms
    assert f"Current stable artifact URL: {navigation_base}/releases/stable-url.txt" in llms
    assert f"Repository: https://github.com/{contract['repository']}" in llms
    assert f"Upstream: https://github.com/{contract['upstream_repository']}" in llms

    if reader.site_dir:
        validate_internal_links(reader.site_dir, navigation_base)


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--site-dir")
    mode.add_argument("--base-url")
    parser.add_argument(
        "--navigation-base",
        help=(
            "Expected navigational base embedded in generated pages. "
            "Defaults to --base-url for deployed checks or GITHUB_METADATA.json "
            "for normal local production builds."
        ),
    )
    args = parser.parse_args()

    contract = load_json(ROOT / "PROJECT_CONTRACT.json")
    metadata = load_json(ROOT / "GITHUB_METADATA.json")
    expected_brand = load_json(ROOT / "docs/assets/brand/brand.json")
    stable = load_json(ROOT / "STABLE_RELEASE.json")
    supported = load_json(ROOT / "SUPPORTED_MINECRAFT.json")
    reader = SiteReader(site_dir=args.site_dir, base_url=args.base_url)
    navigation_base = (
        args.navigation_base or args.base_url or metadata["homepage"]
    ).rstrip("/")

    if args.site_dir:
        validate_site(
            reader,
            contract,
            metadata,
            expected_brand,
            stable,
            supported,
            navigation_base,
        )
    else:
        retryable = (
            AssertionError,
            json.JSONDecodeError,
            OSError,
            UnicodeError,
            urllib.error.HTTPError,
            urllib.error.URLError,
        )
        last_error = None
        for attempt in range(1, REMOTE_ATTEMPTS + 1):
            reader.begin_attempt(attempt)
            try:
                validate_site(
                    reader,
                    contract,
                    metadata,
                    expected_brand,
                    stable,
                    supported,
                    navigation_base,
                )
                break
            except retryable as exc:
                last_error = exc
                if attempt == REMOTE_ATTEMPTS:
                    raise AssertionError(
                        "deployed public-site contract did not converge after "
                        f"{REMOTE_ATTEMPTS} attempts: {exc}"
                    ) from exc
                print(
                    f"Public site not converged (attempt {attempt}/{REMOTE_ATTEMPTS}): {exc}",
                    flush=True,
                )
                time.sleep(REMOTE_DELAY_SECONDS)
        else:
            raise AssertionError(
                f"deployed public-site contract did not converge: {last_error}"
            )

    source = args.site_dir if args.site_dir else args.base_url
    print(f"Public-site contract OK: {source}")


if __name__ == "__main__":
    main()
