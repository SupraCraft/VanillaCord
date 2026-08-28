#!/usr/bin/env python3
"""Apply the canonical public GitHub metadata recorded in GITHUB_METADATA.json.

Default mode is a non-mutating dry run. --apply requires an authenticated GitHub
CLI identity with Administration:write and Pages:write for the repository.
"""

import json
import subprocess
import sys
from pathlib import Path

MODE = sys.argv[1] if len(sys.argv) > 1 else "--dry-run"
if MODE not in {"--dry-run", "--apply"}:
    raise SystemExit("usage: apply-github-metadata.py [--dry-run|--apply]")

metadata = json.loads(Path("GITHUB_METADATA.json").read_text(encoding="utf-8"))
repo = metadata["repository"]


def mutate(method, endpoint, payload):
    if MODE == "--dry-run":
        print(json.dumps({"method": method, "endpoint": endpoint, "payload": payload}, sort_keys=True))
        return
    subprocess.run(
        ["gh", "api", "--method", method, endpoint, "--input", "-"],
        input=json.dumps(payload),
        text=True,
        check=True,
    )


mutate(
    "PATCH",
    f"repos/{repo}",
    {"description": metadata["description"], "homepage": metadata["homepage"]},
)
mutate("PUT", f"repos/{repo}/topics", {"names": metadata["topics"]})

pages = metadata.get("pages", {})
if pages.get("expected_enabled"):
    if pages["source"] == "github-actions":
        payload = {"build_type": "workflow"}
    elif pages["source"] == "branch":
        root = pages["content_root"]
        path = "/docs" if root == "docs/" else "/"
        payload = {"source": {"branch": pages["branch"], "path": path}}
    else:
        raise SystemExit(f"unsupported Pages source: {pages['source']}")

    if MODE == "--dry-run":
        print(json.dumps({"method": "POST-or-PUT", "endpoint": f"repos/{repo}/pages", "payload": payload}, sort_keys=True))
    else:
        probe = subprocess.run(
            ["gh", "api", f"repos/{repo}/pages"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        method = "PUT" if probe.returncode == 0 else "POST"
        mutate(method, f"repos/{repo}/pages", payload)
