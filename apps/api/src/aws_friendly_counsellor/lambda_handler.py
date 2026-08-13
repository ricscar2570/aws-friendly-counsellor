from __future__ import annotations

try:
    from mangum import Mangum
except ImportError:  # pragma: no cover - allows contract generation without Lambda deps
    Mangum = None  # type: ignore[assignment]

from .main import app

handler = Mangum(app, lifespan="off") if Mangum is not None else None
