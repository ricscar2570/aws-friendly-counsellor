# M1.2 Validation Report — Tenant, Project Persistence, and Analysis Versioning

- Project: AWS Friendly Counsellor
- Application version: `3.3.0-m1.2`
- Public contract version: `1.1.0`
- Validation date: 2026-08-01
- Milestone status: **completed**

## Objective

M1.2 introduces durable tenant and project state without moving persistence logic into route handlers. The milestone must provide tenant-scoped access, persistent projects, conflict-safe updates, immutable analysis history, local development storage, and an AWS deployment adapter.

## Delivered domain

### Tenant

- opaque `ten_` identifier;
- unique normalized slug;
- active/suspended status contract;
- persistent creation and retrieval;
- tenant path/header mismatch concealed as `404`.

### Project

- opaque `prj_` identifier;
- mandatory tenant ownership;
- name, description, users, budget, region, and lifecycle status;
- cursor-based list access;
- optimistic revision control;
- stale writes rejected with `409 REVISION_CONFLICT`.

### Analysis version

- opaque `ana_` identifier;
- immutable request and result snapshots;
- monotonically increasing project-local version;
- cursor-based history listing;
- exact historical retrieval;
- archived projects reject new analysis versions.

## Persistence architecture

A domain repository protocol isolates application logic from storage implementation.

### SQLite adapter

- automatic idempotent schema initialization;
- migration ledger with schema version `1`;
- foreign keys enabled on each connection;
- composite tenant/project foreign key for analysis versions;
- WAL mode and busy timeout;
- transactional analysis-version allocation;
- optimistic project updates;
- durable local database file;
- opaque cursor implementation.

### DynamoDB adapter

- tenant-, project-, and analysis-specific key patterns;
- Query-based access paths with no Scan permission;
- transactional tenant slug uniqueness;
- conditional project updates;
- transactional analysis-version allocation with retry;
- consistent reads for individual resources;
- opaque LastEvaluatedKey cursors.

## AWS infrastructure

The SAM template now includes:

- one DynamoDB table with configurable name;
- pay-per-request billing;
- server-side encryption;
- point-in-time recovery;
- retention on deletion and replacement;
- application and data-classification tags;
- Lambda environment selection of the DynamoDB adapter;
- Lambda permissions limited to DescribeTable, GetItem, PutItem, UpdateItem, Query, and TransactWriteItems;
- no DynamoDB Scan or wildcard resource permission;
- existing API Gateway proxy, tracing, metrics, throttling, and Lambda error alarm.

## Public API additions

- `POST /api/v1/tenants`
- `GET /api/v1/tenants/{tenant_id}`
- `POST /api/v1/projects`
- `GET /api/v1/projects`
- `GET /api/v1/projects/{project_id}`
- `PATCH /api/v1/projects/{project_id}`
- `POST /api/v1/projects/{project_id}/analyses`
- `GET /api/v1/projects/{project_id}/analyses`
- `GET /api/v1/projects/{project_id}/analyses/{version}`

The health response now reports the selected persistence backend and availability.

## Contract safeguards

- contract version raised additively from `1.0.0` to `1.1.0`;
- strict request and response models retained;
- generated OpenAPI updated;
- sixteen top-level JSON Schema snapshots generated;
- standard error envelope retained;
- conflict semantics added without changing the envelope;
- resource endpoints document common error responses;
- unknown request fields remain forbidden.

## Test results

```text
46 passed
Total coverage: 94.68%
Required coverage: 90.00%
```

The tests cover:

- existing stateless planning routes and compatibility aliases;
- tenant creation and slug conflicts;
- tenant path/header mismatch;
- project create, list, read, and update;
- cross-tenant read and list isolation;
- stale project revision conflicts;
- project and analysis pagination;
- SQLite persistence after store recreation;
- migration ledger and composite foreign key;
- sequential immutable analysis history;
- preservation of old snapshots after project changes;
- archived-project analysis rejection;
- missing and malformed tenant context;
- invalid cursors;
- DynamoDB adapter success, conflict, retry, pagination, and not-found paths using an isolated boto3 test double;
- SAM persistence, encryption, recovery, retention, and IAM policy structure;
- generated contract drift detection.

## Commands passed

```bash
python -m compileall -q apps packages scripts tests
python scripts/export_contracts.py --check
pytest --cov --cov-report=term-missing -q
python -c "import yaml; yaml.compose(open('infra/sam/template.yaml', encoding='utf-8').read())"
bash -n scripts/package_lambda.sh
python scripts/migrate_local_database.py
SKIP_DEPENDENCIES=true ./scripts/package_lambda.sh
```

## Runtime package validation

The source-layout Lambda package was extracted into an isolated directory. Using only the packaged application and contract directories plus installed runtime libraries, a smoke workflow successfully:

1. created a tenant;
2. created a tenant-scoped project;
3. executed and persisted analysis version `1`.

The package contained only:

- `aws_friendly_counsellor/`;
- `aws_friendly_counsellor_contracts/`.

It did not include repository-only paths such as tests, docs, apps, or packages.

## Environment limitations

The following external validations could not be executed in this environment:

- `sam validate --lint` and `sam build`, because AWS SAM CLI is not installed;
- deployment against a real AWS account;
- DynamoDB integration through LocalStack or an AWS test table;
- a dependency-populated Lambda zip, because the available package index returned no FastAPI distribution;
- Black or Ruff checks, because those executables are not installed.

The repository includes CI steps and declared dependencies for a normal environment. The DynamoDB adapter received extensive isolated unit coverage, but a real integration test remains mandatory before AWS deployment.

## Security assessment

Tenant scope is mandatory throughout the API and repository layers, and storage relations prevent accidental cross-tenant association. However, `X-Tenant-ID` is not yet bound to a managed identity. A caller with a valid API key and knowledge of another tenant ID could attempt that scope.

Therefore M1.2 is **not approved for public multi-tenant SaaS exposure**. M1.4 must bind tenant membership and roles to trusted authorizer claims.

## Definition of Done assessment

| Requirement | Result |
|---|---|
| Tenant domain and persistence | Passed |
| Project domain and persistence | Passed |
| Tenant-scoped repository access | Passed |
| Cross-tenant concealment | Passed |
| Optimistic concurrency | Passed |
| Immutable analysis versions | Passed |
| Sequential version allocation | Passed |
| SQLite local durability | Passed |
| DynamoDB production adapter | Passed at unit/structural level |
| Encrypted and recoverable AWS table | Passed structurally |
| Additive public contracts | Passed |
| Generated schemas synchronized | Passed |
| Coverage at or above 90% | Passed — 94.68% |
| Runtime source package smoke test | Passed |
| Real AWS integration | Deferred due environment |

## Next milestone

M1.3 should introduce environment separation, infrastructure configuration, deployment pipelines, release promotion, database integration testing, and operational rollback controls. It must not begin the frontend before dev, staging, and production foundations are reliable.
