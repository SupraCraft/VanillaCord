#!/usr/bin/env python3
"""Build the VanillaCord GitHub Pages artifact from repository source-of-truth files."""

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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

    write_json(output / "project.json", contract)
    write_json(output / "github.json", metadata)
    write_json(output / "brand.json", brand)
    write_json(
        output / "artifacts.json",
        {
            "schema_version": "1.0.0",
            "repository": contract["repository"],
            "source_version": contract["source_version"],
            "artifact": contract["artifact"],
            "versioning": contract["versioning"],
            "provenance": contract["provenance"],
        },
    )
    write_json(
        output / "compatibility.json",
        {
            "schema_version": "1.0.0",
            "repository": contract["repository"],
            "tiers": contract["validation"]["compatibility_tiers"],
            "operations_document": "https://github.com/SupraCraft/VanillaCord/blob/master/docs/compatibility.md",
            "strategy_document": "https://github.com/SupraCraft/VanillaCord/blob/master/COMPATIBILITY_STRATEGY.md",
            "latest_recorded_report": "https://github.com/SupraCraft/VanillaCord/blob/master/docs/minecraft-compatibility-report.md",
            "note": "This endpoint describes compatibility policy and authoritative report locations; it does not assert that every Minecraft version is supported."
        },
    )

    base = metadata["homepage"].rstrip("/")
    llms = f"""# VanillaCord\n\nVanillaCord patches vanilla Minecraft server JARs for proxy forwarding.\n\nCanonical human entry point: {base}/\nRepository: https://github.com/{contract['repository']}\nUpstream: https://github.com/{contract['upstream_repository']}\nProject contract: {base}/project.json\nGitHub metadata: {base}/github.json\nBrand metadata: {base}/brand.json\nArtifact metadata: {base}/artifacts.json\nCompatibility policy: {base}/compatibility.json\nREADME: https://github.com/{contract['repository']}/blob/master/README.md\nAgent instructions: https://github.com/{contract['repository']}/blob/master/AGENTS.md\n\nPrefer the JSON endpoints and repository contracts over scraping presentation HTML. Bridge is an implementation dependency and is not part of VanillaCord's user-facing identity.\n"""
    (output / "llms.txt").write_text(llms, encoding="utf-8")


if __name__ == "__main__":
    main()
