#!/usr/bin/env python3
"""Inspect class/JAR bytecode for surviving Bridge runtime references.

This is a diagnostic only. It does not modify artifacts or decide whether a
reference is valid; it records exactly where Bridge class names survive so the
release gate can be fixed at the responsible boundary.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import pathlib
import zipfile

TOKENS = (
    b"bridge/Bridge",
    b"bridge/Unchecked",
    b"bridge/Jump",
    b"bridge/",
)
RUNTIME_CLASSES = (
    "bridge/Bridge.class",
    "bridge/Unchecked.class",
    "bridge/Jump.class",
)
MAX_NESTING = 4


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def token_names(data: bytes) -> list[str]:
    return [token.decode("ascii") for token in TOKENS if token in data]


def safe_extract_name(location: str) -> str:
    value = location.replace("!", "__").replace("/", "_").replace("\\", "_")
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)[-220:]


def inspect_zip_bytes(data: bytes, location: str, depth: int, matches: list[dict], inventory: set[str], extracted: pathlib.Path | None) -> None:
    if depth > MAX_NESTING:
        return
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = set(archive.namelist())
            for runtime in RUNTIME_CLASSES:
                if runtime in names:
                    inventory.add(f"{location}!{runtime}")
            for name in sorted(names):
                if name.endswith("/"):
                    continue
                try:
                    entry = archive.read(name)
                except (KeyError, RuntimeError, zipfile.BadZipFile):
                    continue
                child = f"{location}!{name}"
                if name.endswith(".class"):
                    tokens = token_names(entry)
                    if tokens:
                        record = {
                            "location": child,
                            "sha256": sha256(entry),
                            "size": len(entry),
                            "tokens": tokens,
                        }
                        matches.append(record)
                        if extracted is not None:
                            extracted.mkdir(parents=True, exist_ok=True)
                            (extracted / safe_extract_name(child)).write_bytes(entry)
                elif name.endswith((".jar", ".zip")) and zipfile.is_zipfile(io.BytesIO(entry)):
                    inspect_zip_bytes(entry, child, depth + 1, matches, inventory, extracted)
    except zipfile.BadZipFile:
        return


def inspect_path(path: pathlib.Path, matches: list[dict], inventory: set[str], extracted: pathlib.Path | None) -> dict:
    result = {
        "input": str(path),
        "exists": path.exists(),
        "kind": "missing",
        "sha256": None,
        "size": None,
    }
    if not path.exists():
        return result

    if path.is_file():
        data = path.read_bytes()
        result.update({"kind": "file", "sha256": sha256(data), "size": len(data)})
        if path.suffix == ".class":
            tokens = token_names(data)
            if tokens:
                matches.append({
                    "location": str(path),
                    "sha256": sha256(data),
                    "size": len(data),
                    "tokens": tokens,
                })
        elif zipfile.is_zipfile(io.BytesIO(data)):
            inspect_zip_bytes(data, str(path), 0, matches, inventory, extracted)
        return result

    result["kind"] = "directory"
    count = 0
    for file in sorted(path.rglob("*")):
        if not file.is_file():
            continue
        if file.suffix not in {".class", ".jar", ".zip"}:
            continue
        count += 1
        data = file.read_bytes()
        if file.suffix == ".class":
            tokens = token_names(data)
            if tokens:
                matches.append({
                    "location": str(file),
                    "sha256": sha256(data),
                    "size": len(data),
                    "tokens": tokens,
                })
                if extracted is not None:
                    extracted.mkdir(parents=True, exist_ok=True)
                    (extracted / safe_extract_name(str(file))).write_bytes(data)
        elif zipfile.is_zipfile(io.BytesIO(data)):
            inspect_zip_bytes(data, str(file), 0, matches, inventory, extracted)
    result["scanned_files"] = count
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", help="Class files, JAR/ZIP files, or directories to inspect")
    parser.add_argument("--json", dest="json_path", required=True)
    parser.add_argument("--extract-matches", dest="extract_dir")
    parser.add_argument("--label", default="runtime-closure")
    args = parser.parse_args()

    matches: list[dict] = []
    inventory: set[str] = set()
    extracted = pathlib.Path(args.extract_dir) if args.extract_dir else None
    inputs = [inspect_path(pathlib.Path(value), matches, inventory, extracted) for value in args.inputs]

    # De-duplicate identical records that can arise when a directory and one of
    # its child JARs are both supplied explicitly.
    unique = {}
    for record in matches:
        key = (record["location"], tuple(record["tokens"]))
        unique[key] = record
    matches = [unique[key] for key in sorted(unique)]

    report = {
        "schema": "vanillacord-runtime-closure-diagnostic/1",
        "label": args.label,
        "tokens": [token.decode("ascii") for token in TOKENS],
        "inputs": inputs,
        "matches": matches,
        "runtimeClassesPresent": sorted(inventory),
        "summary": {
            "matchCount": len(matches),
            "bridgeBridgeReferenceCount": sum("bridge/Bridge" in item["tokens"] for item in matches),
            "bridgeUncheckedReferenceCount": sum("bridge/Unchecked" in item["tokens"] for item in matches),
            "bridgeJumpReferenceCount": sum("bridge/Jump" in item["tokens"] for item in matches),
            "runtimeClassCount": len(inventory),
        },
    }

    output = pathlib.Path(args.json_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"[{args.label}] matches={len(matches)} runtime-classes={len(inventory)}")
    for record in matches:
        print(f"REF {record['location']} :: {', '.join(record['tokens'])}")
    for location in sorted(inventory):
        print(f"CLASS {location}")
    print(f"report={output}")


if __name__ == "__main__":
    main()
