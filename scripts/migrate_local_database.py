#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "apps/api/src", ROOT / "packages/contracts/python"):
    sys.path.insert(0, str(path))

os.environ.setdefault("STORAGE_BACKEND", "sqlite")

from aws_friendly_counsellor.infrastructure.persistence import get_store  # noqa: E402


def main() -> int:
    store = get_store()
    store.initialize()
    if not store.health_check():
        print("Persistence health check failed", file=sys.stderr)
        return 1
    print(f"Initialized {store.backend_name} persistence successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
