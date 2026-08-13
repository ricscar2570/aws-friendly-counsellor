#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "apps/api/src", ROOT / "packages/contracts/python"):
    sys.path.insert(0, str(path))

from aws_friendly_counsellor.main import app  # noqa: E402
from aws_friendly_counsellor_contracts import TOP_LEVEL_CONTRACT_MODELS  # noqa: E402

OPENAPI_PATH = ROOT / "packages/contracts/openapi/v1/openapi.json"
SCHEMA_DIR = ROOT / "packages/contracts/jsonschema/v1"


def _serialize(payload: object) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def expected_files() -> dict[Path, str]:
    outputs = {OPENAPI_PATH: _serialize(app.openapi())}
    for model in TOP_LEVEL_CONTRACT_MODELS:
        filename = f"{model.__name__}.schema.json"
        outputs[SCHEMA_DIR / filename] = _serialize(model.model_json_schema())
    return outputs


def check_contracts(outputs: dict[Path, str]) -> int:
    mismatches: list[str] = []
    for path, expected in outputs.items():
        if not path.exists():
            mismatches.append(f"missing: {path.relative_to(ROOT)}")
        elif path.read_text(encoding="utf-8") != expected:
            mismatches.append(f"outdated: {path.relative_to(ROOT)}")
    expected_paths = set(outputs)
    for path in SCHEMA_DIR.glob("*.schema.json"):
        if path not in expected_paths:
            mismatches.append(f"stale: {path.relative_to(ROOT)}")
    if mismatches:
        print("Contract snapshot check failed:")
        for mismatch in mismatches:
            print(f"- {mismatch}")
        return 1
    print("Contract snapshots are current.")
    return 0


def write_contracts(outputs: dict[Path, str]) -> None:
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    OPENAPI_PATH.parent.mkdir(parents=True, exist_ok=True)
    expected_paths = set(outputs)
    for path in SCHEMA_DIR.glob("*.schema.json"):
        if path not in expected_paths:
            path.unlink()
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
        print(f"Wrote {path.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export or verify public API contracts.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when committed OpenAPI/JSON Schema snapshots are not current.",
    )
    args = parser.parse_args()
    outputs = expected_files()
    if args.check:
        return check_contracts(outputs)
    write_contracts(outputs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
