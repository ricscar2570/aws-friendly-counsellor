# API and contract versioning

The public HTTP path remains `/api/v1`. M1.4 raises the additive contract package from `1.2.0` to `1.3.0`.

## Changes in contract 1.3.0

Added:

- `GET /api/v1/me` identity response;
- tenant membership create/list/update contracts;
- tenant audit-list contract;
- `viewer`, `editor`, `admin`, and `owner` role vocabulary;
- membership `active`/`suspended` status vocabulary.

Existing planning, tenant, project, and analysis request/response shapes remain compatible. Authorization requirements are stronger: protected deployed routes require Cognito bearer identity, and tenant resource routes additionally require durable membership.

## Compatibility rules

- additive response fields/endpoints may raise the contract minor version;
- existing v1 request fields may not silently change meaning;
- removing/renaming fields requires a new API path or major contract version;
- generated OpenAPI and JSON Schema snapshots must match application code;
- authorization tightening may occur when it closes a documented security gap and is called out in the milestone notes;
- legacy `/api/analyze`, `/api/iac`, and `/api/narrative` aliases remain deprecated and outside public OpenAPI.
