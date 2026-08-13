from __future__ import annotations


class DomainError(Exception):
    code = "DOMAIN_ERROR"
    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    code = "NOT_FOUND"
    status_code = 404


class ConflictError(DomainError):
    code = "CONFLICT"
    status_code = 409


class RevisionConflictError(ConflictError):
    code = "REVISION_CONFLICT"


class PersistenceUnavailableError(DomainError):
    code = "PERSISTENCE_UNAVAILABLE"
    status_code = 503
