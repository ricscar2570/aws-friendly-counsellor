# Public API contracts

This package is the source of truth for communication between the API, future web client, automated tests, and external integrations.

- `python/aws_friendly_counsellor_contracts`: strict Pydantic models;
- `openapi/v1/openapi.json`: generated OpenAPI snapshot;
- `jsonschema/v1`: generated top-level JSON Schema snapshots.

Contract `1.3.0` includes stateless planning, managed identity, tenant membership authorization, persistent project/analysis resources, and tenant audit responses.

Generate snapshots:

```bash
python scripts/export_contracts.py
```

Verify committed snapshots:

```bash
python scripts/export_contracts.py --check
```

Generated files must not be edited manually. Breaking changes require a new API path rather than silent mutation of v1.
