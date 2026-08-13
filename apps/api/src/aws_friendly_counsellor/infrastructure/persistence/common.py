from __future__ import annotations

import base64
import json
import re
from datetime import datetime, timezone
from uuid import uuid4

_ID_RE = re.compile(r"^[a-z]{3}_[a-f0-9]{24}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:24]}"


def is_valid_resource_id(value: str, prefix: str) -> bool:
    return bool(_ID_RE.fullmatch(value)) and value.startswith(f"{prefix}_")


def encode_cursor(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> dict[str, object]:
    try:
        padding = "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode((cursor + padding).encode("ascii"))
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid pagination cursor") from exc
    if not isinstance(payload, dict):
        raise ValueError("Invalid pagination cursor")
    return payload
