from __future__ import annotations

import os
import threading

from ...domain.repositories import PersistenceStore
from .dynamodb_store import DynamoDBStore
from .sqlite_store import SQLiteStore

_store: PersistenceStore | None = None
_store_signature: tuple[str, str, str | None] | None = None
_lock = threading.Lock()


def _configuration() -> tuple[str, str, str | None]:
    backend = os.getenv("STORAGE_BACKEND", "sqlite").strip().lower()
    if backend == "dynamodb":
        target = os.getenv("DYNAMODB_TABLE_NAME", "").strip()
        region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    else:
        target = os.getenv("SQLITE_PATH", ".local/aws-friendly-counsellor.db").strip()
        region = None
    return backend, target, region


def get_store() -> PersistenceStore:
    global _store, _store_signature
    signature = _configuration()
    with _lock:
        if _store is not None and _store_signature == signature:
            return _store
        if _store is not None:
            _store.close()
        backend, target, region = signature
        if backend == "sqlite":
            store: PersistenceStore = SQLiteStore(target)
        elif backend == "dynamodb":
            if not target:
                raise RuntimeError("DYNAMODB_TABLE_NAME is required for DynamoDB storage")
            store = DynamoDBStore(target, region_name=region)
        else:
            raise RuntimeError(f"Unsupported STORAGE_BACKEND: {backend}")
        store.initialize()
        _store = store
        _store_signature = signature
        return store


def reset_store() -> None:
    global _store, _store_signature
    with _lock:
        if _store is not None:
            _store.close()
        _store = None
        _store_signature = None
