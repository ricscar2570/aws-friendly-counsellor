# ADR 0001 — Establish a monorepo and contract-first API boundary

- Status: Accepted
- Date: 2026-07-30

## Context

The M0 backend was deployable but used a flat `backend` directory, unversioned `/api/*` routes, and untyped dictionaries as public responses. Adding a frontend, persistence, and external integrations on that foundation would create hidden coupling.

## Decision

Adopt a monorepo with `apps`, `packages`, and `infra` boundaries. Keep FastAPI as a modular monolith. Publish the first explicit API under `/api/v1`. Store strict Pydantic request and response models in a shared contract package and generate OpenAPI and JSON Schema snapshots from the running application.

Keep old endpoints temporarily as undocumented aliases with deprecation headers. Package Lambda through an AWS SAM custom Makefile builder so shared contracts are included without copying the full repository.

## Consequences

Positive:

- frontend and backend can share a versioned source of truth;
- response serialization is validated rather than assumed;
- breaking changes become visible;
- Lambda packaging remains explicit;
- future domains can be added without starting with microservices.

Costs:

- imports and build scripts are more structured;
- contract snapshots must be regenerated intentionally;
- temporary legacy route maintenance is required.
