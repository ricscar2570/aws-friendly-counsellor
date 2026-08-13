from __future__ import annotations

import argparse
import re

PRODUCTION_TAG = re.compile(r"^v\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
IMMUTABLE_REF = re.compile(r"^(?:[0-9a-fA-F]{40}|v\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)$")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", choices=["dev", "staging", "production"], required=True)
    parser.add_argument("--ref", required=True)
    args = parser.parse_args()

    pattern = PRODUCTION_TAG if args.environment == "production" else IMMUTABLE_REF
    if not pattern.fullmatch(args.ref):
        expected = "a semantic version tag" if args.environment == "production" else "a full commit SHA or semantic version tag"
        raise SystemExit(f"Invalid {args.environment} release ref {args.ref!r}; expected {expected}")
    print(args.ref)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
