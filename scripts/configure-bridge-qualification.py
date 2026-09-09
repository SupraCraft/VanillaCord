#!/usr/bin/env python3
"""Validate a Bridge consumer-qualification manifest and export its exact version."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SCHEMA = "vanillacord-bridge-consumer-qualification/1"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:-rc\.\d+)?$")


def fail(message: str) -> None:
    raise SystemExit(f"Bridge consumer qualification invalid: {message}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--ref", required=True)
    parser.add_argument("--github-env", required=True)
    args = parser.parse_args()

    data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        fail(f"schema must be {SCHEMA}")
    if data.get("bridge_repository") != "SupraCraft/Bridge":
        fail("bridge_repository must be SupraCraft/Bridge")
    if data.get("purpose") != "bridge-release-consumer-gate":
        fail("purpose must be bridge-release-consumer-gate")

    version = data.get("bridge_version")
    if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
        fail("bridge_version must be an exact stable or release-candidate version")

    expected_ref = f"refs/heads/qualification/bridge/{version}"
    if args.ref != expected_ref:
        fail(f"branch must be {expected_ref}; got {args.ref}")

    with open(args.github_env, "a", encoding="utf-8") as handle:
        handle.write(f"BRIDGE_VERSION={version}\n")
        handle.write("BRIDGE_QUALIFICATION_MODE=true\n")
        handle.write("VANILLACORD_INCLUDE_SNAPSHOT=false\n")
        handle.write("VANILLACORD_BOOT_SMOKE=true\n")
        handle.write("VANILLACORD_REQUIRED_SUPPORTED=1.21.11 1.20.6 1.20.4 1.19.4 1.18.2\n")
        handle.write("VANILLACORD_BEST_EFFORT_LEGACY=none\n")

    print(f"Qualified Bridge input configured: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
