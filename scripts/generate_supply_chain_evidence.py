from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "supply-chain"
SBOM_PATH = OUTPUT_DIR / "sbom.cdx.json"
CHECKSUM_PATH = OUTPUT_DIR / "evidence.sha256"
LOCK_FILES = (
    ROOT / "apps/api/requirements.txt",
    ROOT / "requirements-dev.txt",
    ROOT / ".python-version",
)
ACTION_FILES = tuple(sorted((ROOT / ".github/workflows").glob("*.yml")))
PIN_RE = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s;]+)$")
ACTION_RE = re.compile(r"^\s*-?\s*uses:\s*([^\s@]+)@([^\s#]+)", re.MULTILINE)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_requirements(path: Path) -> dict[str, str]:
    packages: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("-r "):
            continue
        match = PIN_RE.fullmatch(line)
        if not match:
            raise ValueError(f"Dependency is not an exact pin in {path.relative_to(ROOT)}: {line}")
        name, version = match.groups()
        packages[name.lower().replace("_", "-")] = version
    return packages


def _collect_actions() -> list[dict[str, str]]:
    found: dict[str, str] = {}
    for path in ACTION_FILES:
        for repository, ref in ACTION_RE.findall(path.read_text(encoding="utf-8")):
            previous = found.get(repository)
            if previous is not None and previous != ref:
                raise ValueError(f"GitHub action {repository} uses multiple refs: {previous}, {ref}")
            found[repository] = ref
    return [
        {"repository": repository, "ref": found[repository]}
        for repository in sorted(found)
    ]


def _sbom_bytes() -> bytes:
    runtime = _read_requirements(ROOT / "apps/api/requirements.txt")
    development = _read_requirements(ROOT / "requirements-dev.txt")
    packages = dict(runtime)
    packages.update(development)
    components = []
    for name in sorted(packages):
        scopes: list[str] = []
        if name in runtime:
            scopes.append("runtime")
        if name in development:
            scopes.append("development")
        components.append(
            {
                "type": "library",
                "bom-ref": f"pkg:pypi/{name}@{packages[name]}",
                "name": name,
                "version": packages[name],
                "purl": f"pkg:pypi/{name}@{packages[name]}",
                "properties": [
                    {"name": "awsfc:dependency-scope", "value": ",".join(scopes)}
                ],
            }
        )
    document = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": "urn:uuid:0df6cd50-f6f0-4a65-b1f8-e9338791cf14",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "name": "aws-friendly-counsellor",
                "version": "3.5.0-m1.4",
            },
            "properties": [
                {
                    "name": "awsfc:evidence-model",
                    "value": "version-resolved-python-locks-and-reviewed-github-action-refs",
                },
                {
                    "name": "awsfc:github-actions",
                    "value": json.dumps(_collect_actions(), separators=(",", ":"), sort_keys=True),
                },
            ],
        },
        "components": components,
    }
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _checksum_bytes(sbom: bytes) -> bytes:
    files = [*LOCK_FILES, *ACTION_FILES]
    lines = []
    for path in sorted(files, key=lambda item: item.relative_to(ROOT).as_posix()):
        lines.append(f"{_sha256(path.read_bytes())}  {path.relative_to(ROOT).as_posix()}")
    lines.append(f"{_sha256(sbom)}  {SBOM_PATH.relative_to(ROOT).as_posix()}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    sbom = _sbom_bytes()
    checksums = _checksum_bytes(sbom)
    expected = {SBOM_PATH: sbom, CHECKSUM_PATH: checksums}
    if args.check:
        problems = []
        for path, data in expected.items():
            if not path.exists():
                problems.append(f"missing: {path.relative_to(ROOT)}")
            elif path.read_bytes() != data:
                problems.append(f"outdated: {path.relative_to(ROOT)}")
        if problems:
            print("Supply-chain evidence check failed:")
            for problem in problems:
                print(f"- {problem}")
            return 1
        print("Supply-chain evidence is current.")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path, data in expected.items():
        path.write_bytes(data)
        print(f"Wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
