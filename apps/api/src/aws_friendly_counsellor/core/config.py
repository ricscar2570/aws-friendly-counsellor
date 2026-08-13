from __future__ import annotations

import os
from dataclasses import dataclass

_ALLOWED_ENVIRONMENTS = {"local", "test", "dev", "staging", "production"}
_ALLOWED_LOG_LEVELS = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}


def _environment(name: str, default: str) -> str:
    value = os.getenv(name, default).strip().lower()
    if value not in _ALLOWED_ENVIRONMENTS:
        raise RuntimeError(
            f"{name} must be one of {sorted(_ALLOWED_ENVIRONMENTS)}, got {value!r}"
        )
    return value


def _log_level() -> str:
    value = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    if value not in _ALLOWED_LOG_LEVELS:
        raise RuntimeError(
            f"LOG_LEVEL must be one of {sorted(_ALLOWED_LOG_LEVELS)}, got {value!r}"
        )
    return value


def _origins() -> tuple[str, ...]:
    origins = tuple(
        origin.strip().rstrip("/")
        for origin in os.getenv(
            "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173"
        ).split(",")
        if origin.strip()
    )
    if not origins:
        raise RuntimeError("ALLOWED_ORIGINS must contain at least one origin")
    if "*" in origins:
        raise RuntimeError("Wildcard CORS origins are not permitted")
    return origins


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "AWS Friendly Counsellor"
    app_version: str = "3.5.0-m1.4"
    api_version: str = "v1"
    contract_version: str = "1.3.0"
    environment: str = "local"
    release_version: str = "local"
    git_sha: str = "unknown"
    log_level: str = "INFO"
    allowed_origins: tuple[str, ...] = (
        "http://localhost:3000",
        "http://localhost:5173",
    )


def load_settings() -> Settings:
    return Settings(
        environment=_environment("APP_ENVIRONMENT", "local"),
        release_version=os.getenv("RELEASE_VERSION", "local").strip() or "local",
        git_sha=os.getenv("GIT_SHA", "unknown").strip() or "unknown",
        log_level=_log_level(),
        allowed_origins=_origins(),
    )


settings = load_settings()
