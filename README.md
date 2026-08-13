# AWS Friendly Counsellor

AWS Friendly Counsellor is evolving from a deterministic AWS planning API into a transparent advisory SaaS. This repository is the **M1.4 managed identity, tenant authorization, durable audit, threat-model, and supply-chain-evidence milestone**.

## Milestone status

- M0 backend consolidation: complete
- M1.1 monorepo and API contracts: complete
- M1.2 tenant persistence and immutable analysis history: complete
- M1.3 isolated environments and controlled delivery: complete
- M1.4 managed identity, authorization, audit, and threat model: complete locally
- real AWS M1.4 deployment proof: pending an AWS-capable environment
- M2 production frontend: not started

The API classifies project descriptions, recommends AWS services, estimates conservative cost ranges, creates implementation guidance, emits Terraform baselines, generates HTML architecture reports, and persists tenant-scoped projects with immutable analysis versions.

## Repository layout

```text
apps/api/                       FastAPI modular monolith and Lambda entry point
apps/web/                       Reserved boundary for the M2 frontend
packages/contracts/             Pydantic, OpenAPI, and JSON Schema contracts
infra/sam/                      Environment-aware application stack and profiles
infra/bootstrap/                GitHub OIDC, artifact bucket, and deployment roles
scripts/                        Contracts, database, deployment, evidence, smoke, packaging
supply-chain/                   CycloneDX SBOM and deterministic evidence checksums
tests/                          API, persistence, authz, infrastructure, delivery tests
docs/                           Architecture, operations, security, threat model, reports
```

## Public API

Planning routes require authenticated identity:

- `POST /api/v1/analyze`
- `POST /api/v1/iac`
- `POST /api/v1/narrative`
- `GET /api/v1/me`

Tenant and authorization routes:

- `POST /api/v1/tenants`
- `GET /api/v1/tenants/{tenant_id}`
- `GET /api/v1/tenants/{tenant_id}/memberships`
- `POST /api/v1/tenants/{tenant_id}/memberships`
- `PATCH /api/v1/tenants/{tenant_id}/memberships/{subject}`
- `GET /api/v1/tenants/{tenant_id}/audit`

Project routes:

- `POST /api/v1/projects`
- `GET /api/v1/projects`
- `GET /api/v1/projects/{project_id}`
- `PATCH /api/v1/projects/{project_id}`
- `POST /api/v1/projects/{project_id}/analyses`
- `GET /api/v1/projects/{project_id}/analyses`
- `GET /api/v1/projects/{project_id}/analyses/{version}`

Operational routes remain public:

- `GET /health/live` — process liveness without persistence;
- `GET /health/ready` — persistence readiness;
- `GET /health` — combined compatibility check.

Responses expose `X-Request-ID`, `X-API-Version`, `X-App-Environment`, and `X-Release-Version`.

## Identity and tenant authorization

Deployed protected routes use a Cognito user pool authorizer at API Gateway. The application derives the principal from verified authorizer claims. For tenant-scoped routes, `X-Tenant-ID` only selects a tenant; it grants no authority.

Authorization comes from durable membership:

- `viewer`: read tenant/projects/analysis;
- `editor`: viewer + create/update projects and create analyses;
- `admin`: editor + membership/audit reads and viewer/editor membership management;
- `owner`: full tenant membership authority, except self-demotion in M1.4.

See `docs/IDENTITY_AUTHORIZATION.md` and `docs/THREAT_MODEL.md`.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
export APP_ENVIRONMENT=local
export ALLOW_LOCAL_IDENTITY=true
export LOCAL_IDENTITY_SUBJECT=00000000-0000-4000-8000-000000000001
export PYTHONPATH=apps/api/src:packages/contracts/python
python scripts/migrate_local_database.py
uvicorn aws_friendly_counsellor.main:app --reload
```

The debug identity mechanism is hard-disabled when `APP_ENVIRONMENT` is `dev`, `staging`, or `production`.

## Quality gate

```bash
make validate
```

The gate compiles Python, verifies generated contracts, validates environment/deployment invariants, verifies committed supply-chain evidence, runs the test suite, and enforces at least 90% total line coverage.

## Deployment environments

`dev`, `staging`, and `production` use distinct CloudFormation stacks, API stages, Cognito user pools/clients, Lambda resources, DynamoDB tables, alarms, log retention, concurrency settings, and GitHub environments.

```bash
RELEASE_VERSION=v3.5.0 \
GIT_SHA=$(git rev-parse HEAD) \
ALLOWED_ORIGINS=https://dev.example.com \
SAM_ARTIFACT_BUCKET=replace-me \
CLOUDFORMATION_EXECUTION_ROLE_ARN=arn:aws:iam::123456789012:role/replace-me \
./scripts/deploy_environment.sh dev
```

The dev profile permits Cognito self-registration; staging and production do not. Production enables both DynamoDB and Cognito deletion protection. User pools and DynamoDB data are retained on stack removal/replacement.

Production Lambda artifacts are built with `sam build --use-container` for the arm64 target. Semantic tags build once, then promote that exact artifact through staging and production.

## Delivery model

- GitHub uses OIDC temporary AWS credentials, never stored AWS access keys;
- deployment and CloudFormation execution roles are distinct;
- Lambda versions are published behind `live`;
- CodeDeploy can shift traffic gradually and roll back on alias errors/throttles;
- CloudFormation failures roll back;
- public liveness/readiness/release smoke tests run after deployment;
- the release artifact includes `supply-chain/sbom.cdx.json` and `supply-chain/evidence.sha256`.

See `docs/CI_CD.md`, `docs/ENVIRONMENTS.md`, and `docs/ROLLBACK_RUNBOOK.md`.

## Security boundary

M1.4 closes the M1.3 public multi-tenant identity gap: valid bearer identity alone is insufficient for tenant access; a durable active membership with the required role is mandatory. Audited mutations write application state and audit evidence transactionally.

M1.4 does **not** claim production accreditation. Optional MFA does not mean every user has MFA, and this environment could not execute real Cognito/API Gateway/DynamoDB integration tests, a live canary rollback, a penetration test, or account-level CloudTrail/SIEM validation.

## Validation boundary

Local validation can prove application behavior, contracts, dual persistence logic, authorization rules, configuration invariants, workflow structure, deterministic evidence, package layout, and archive integrity. Real AWS deployment proof must still run in CI/staging where SAM, Docker, AWS credentials, Cognito, API Gateway, and DynamoDB are available.

## License

MIT. See `LICENSE`.
