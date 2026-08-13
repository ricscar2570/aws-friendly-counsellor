from __future__ import annotations

import re
import uuid

from fastapi import Request

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def resolve_request_id(request: Request) -> str:
    candidate = request.headers.get("X-Request-ID", "").strip()
    if candidate and _REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate
    return str(uuid.uuid4())
