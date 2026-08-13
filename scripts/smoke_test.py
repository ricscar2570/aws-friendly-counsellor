from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any


def _get_json(url: str, timeout: float) -> tuple[int, dict[str, Any]]:
    request = urllib.request.Request(url, headers={"User-Agent": "awsfc-smoke-test/1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GET {url} returned {exc.code}: {body}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a deployed AWSFC environment")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--expected-environment", required=True)
    parser.add_argument("--expected-release", required=True)
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    for endpoint, expected_check in (
        ("/health/live", "liveness"),
        ("/health/ready", "readiness"),
    ):
        status, body = _get_json(base_url + endpoint, args.timeout)
        if status != 200:
            raise RuntimeError(f"{endpoint} returned status {status}")
        expected = {
            "status": "healthy",
            "check": expected_check,
            "environment": args.expected_environment,
            "release_version": args.expected_release,
        }
        mismatches = {
            key: {"expected": value, "actual": body.get(key)}
            for key, value in expected.items()
            if body.get(key) != value
        }
        if mismatches:
            raise RuntimeError(f"{endpoint} mismatch: {json.dumps(mismatches)}")
    print(
        json.dumps(
            {
                "status": "passed",
                "base_url": base_url,
                "environment": args.expected_environment,
                "release": args.expected_release,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
