# M1.1 Validation Report — Monorepo and API Contracts

- Project: AWS Friendly Counsellor
- Application version: `3.2.0-m1.1`
- Public contract version: `1.0.0`
- Validation date: 2026-07-30
- Milestone status: **completed**

## Objective

M1.1 converts the consolidated M0 backend into a stable monorepo foundation without beginning persistence or frontend implementation prematurely. The milestone establishes ownership boundaries, a versioned public API, strict shared contracts, reproducible contract snapshots, and deployment packaging compatible with the new structure.

## Delivered structure

```text
apps/api/        FastAPI modular monolith and Lambda entry point
apps/web/        reserved M2 frontend boundary
packages/contracts/
                 shared Pydantic contracts, OpenAPI, JSON Schema
infra/sam/       AWS SAM deployment definition
scripts/         contract export and Lambda packaging
tests/           API, contract, service, security, and repository checks
docs/            architecture, versioning, security, ADRs, reports
```

The superseded flat `backend/` tree and duplicate root `template.yaml` were removed.

## Public API contract

Supported documented endpoints:

- `GET /`
- `GET /health`
- `POST /api/v1/analyze`
- `POST /api/v1/iac`
- `POST /api/v1/narrative`

Temporary legacy aliases remain operational but are omitted from OpenAPI:

- `/api/analyze`
- `/api/iac`
- `/api/narrative`

Legacy responses include `Deprecation: true` and a `successor-version` link.

## Contract safeguards

- Request and response objects are strict Pydantic models.
- Unknown request fields are rejected.
- API responses are validated before serialization.
- Error responses use one stable envelope.
- Metadata includes both application and contract versions.
- External request IDs are accepted only when they match the safe character and length policy.
- OpenAPI and seven top-level JSON Schema files are generated from code.
- CI fails when committed contract snapshots drift from the application.

## Test results

```text
27 passed
Total coverage: 94.90%
Required coverage: 90.00%
```

Validated behavior includes:

- root and health metadata;
- versioned analyze, IaC, and narrative endpoints;
- all eleven supported classifier/recommender profiles;
- low, medium, and high budget variants;
- essential and advanced guide variants;
- non-zero cost breakdown behavior;
- Terraform API Gateway/Lambda integration baseline;
- strict validation and standard error envelopes;
- authentication failure contract;
- request-ID propagation and sanitization;
- all three compatibility aliases and deprecation headers;
- OpenAPI path exposure and error schemas;
- generated contract snapshot consistency;
- monorepo boundaries and removal of the legacy tree;
- SAM template YAML syntax and custom builder configuration.

## Packaging validation

The standalone packaging script was executed in source-layout verification mode. The resulting zip was extracted into an isolated directory and passed an API smoke test using only the packaged application and shared contract directories.

The archive was checked to contain:

- `aws_friendly_counsellor/`;
- `aws_friendly_counsellor_contracts/`.

It was checked not to contain repository-only directories such as tests, docs, apps, or packages.

The Lambda handler module path was also verified with a temporary Mangum-compatible stand-in because Mangum is not installed in the validation environment.

## Deployment correction found during validation

The initial M1.1 SAM draft listed only individual API routes. That would have left `/docs`, `/redoc`, and `/api/v1/openapi.json` unreachable after deployment. The final template uses root and `/{proxy+}` events so FastAPI remains the route source of truth.

The API Gateway wildcard CORS block was removed. CORS is now enforced once, by FastAPI, using the configured allowlist rather than a conflicting `*` policy.

## Commands passed

```bash
python -m compileall -q apps packages scripts tests
python scripts/export_contracts.py --check
pytest --cov --cov-report=term-missing -q
SKIP_DEPENDENCIES=true ./scripts/package_lambda.sh
```

The SAM template was parsed successfully by PyYAML as a structural syntax check.

## Environment limitations

The following external validations could not be executed in this environment:

- `sam validate --lint` and `sam build`, because AWS SAM CLI is not installed;
- a full dependency-populated Lambda zip, because the available package index returned no distributions for the declared FastAPI dependency;
- a real Mangum invocation, because Mangum is not installed locally.

These limitations do not affect the source, contract, API, structural, or source-layout packaging tests. They remain mandatory checks in a normal CI/deployment environment with dependency and AWS SAM access.

## Definition of Done assessment

| Requirement | Result |
|---|---|
| Monorepo boundaries established | Passed |
| API versioned under `/api/v1` | Passed |
| Shared strict contracts | Passed |
| OpenAPI and JSON Schema reproducible | Passed |
| Legacy compatibility controlled | Passed |
| Lambda packaging adapted to monorepo | Passed |
| CI updated | Passed |
| Coverage gate at or above 90% | Passed — 94.90% |
| Architecture/versioning ADR documentation | Passed |
| M1.2 persistence work avoided | Passed |

## Next milestone

M1.2 should introduce tenant, project, analysis, and version persistence. It must build on these contracts rather than adding database logic directly to route handlers.
