# Contract changelog

## 1.3.0 — 2026-08-13

- Added authenticated identity response.
- Added tenant membership create, list, and revision-controlled update contracts.
- Added tenant audit-list contract.
- Added viewer/editor/admin/owner role and membership-status vocabularies.
- Preserved existing planning, tenant, project, and immutable-analysis request/response shapes.

## 1.2.0 — 2026-08-01

- Added environment and release identity to root and health responses.
- Added separate liveness and readiness health-check values.
- Preserved the combined `/health` compatibility response.
- Kept all planning and persistence request contracts backward compatible.

## 1.1.0 — 2026-08-01

- Added tenant create and read contracts.
- Added project create, list, read, and revision-controlled update contracts.
- Added immutable project-analysis create, list, and read contracts.
- Added opaque pagination cursors.
- Added persistence backend and status to health responses.
- Added conflict-response documentation while preserving the error envelope.

## 1.0.0 — 2026-07-30

- Established the first explicit public contract for `/api/v1`.
- Added strict planning request, success-response, metadata, and error models.
- Added reproducible OpenAPI and JSON Schema snapshots.
