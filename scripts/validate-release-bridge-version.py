#!/usr/bin/env python3
"""Fail closed unless a Bridge release input is an RC or stable coordinate."""

from __future__ import annotations

import re
import sys

RELEASE_GRADE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-rc\.[1-9][0-9]*)?$")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate-release-bridge-version.py <bridge-version>", file=sys.stderr)
        return 2

    version = sys.argv[1].strip()
    if not RELEASE_GRADE.fullmatch(version):
        print(
            "Release Bridge version must be an exact stable X.Y.Z or release candidate X.Y.Z-rc.N; "
            f"got {version!r}",
            file=sys.stderr,
        )
        return 1

    print(f"Release-grade Bridge version OK: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
