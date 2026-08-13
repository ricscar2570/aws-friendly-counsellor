# Architecture — M1.4

## Architectural style

AWS Friendly Counsellor remains a modular FastAPI monolith with interchangeable SQLite and DynamoDB persistence adapters. M1.4 adds a managed application identity boundary, durable tenant membership authorization, transactional audit evidence, and supply-chain evidence without changing the deterministic planning engine.

## Runtime request flow

1. API Gateway receives a request in the environment-specific stage.
2. Public root/health/preflight methods bypass application identity; protected proxy methods use the Cognito authorizer.
3. Cognito/API Gateway validates the bearer token and supplies verified identity claims.
4. Lambda alias `live` invokes the published application version through Mangum.
5. FastAPI resolves the request ID and derives the `Principal` from the authorizer claims.
6. Tenant-scoped routes treat `X-Tenant-ID` only as a selector, load the subject's durable membership, and enforce the role requirement.
7. Strict Pydantic contracts validate the request.
8. Deterministic planning services run or resource services mutate tenant data.
9. Audited mutations persist state and the audit event atomically.
10. Responses expose request, API, environment, and release identity headers.

## Environment topology

Each of `dev`, `staging`, and `production` is a separate CloudFormation stack with its own:

- API Gateway stage and Cognito authorizer;
- Cognito user pool and app client;
- Lambda function, versions, and `live` alias;
- DynamoDB table;
- log group, retention, alarms, and concurrency allocation;
- GitHub environment and AWS OIDC role.

Application data and users are not promoted between environments. Only one immutable release artifact is promoted.

## Identity and authorization model

The Cognito `sub` is the stable application subject. Tenant membership is application data rather than a Cognito group because one identity may have different roles in different tenants. The persisted membership tuple is `(tenant_id, subject, role, status, revision)`.

Role authorization is deliberately server-side. Browser-supplied tenant IDs, role names, or user profile fields do not establish authority.

## Persistence model

The M1.2 tenant/project/analysis model is preserved and extended with memberships and audit events.

DynamoDB single-table keys include:

- tenant: `pk=TENANT#<tenant_id>`, `sk=METADATA`;
- membership: `pk=TENANT#<tenant_id>`, `sk=MEMBER#<subject>`;
- project: `pk=TENANT#<tenant_id>`, `sk=PROJECT#<project_id>`;
- analysis: `pk=TENANT#<tenant_id>#PROJECT#<project_id>`, `sk=ANALYSIS#<version>`;
- audit: `pk=TENANT#<tenant_id>`, `sk=AUDIT#<timestamp>#<audit_id>`.

SQLite schema migration 2 creates memberships and audit events while preserving existing tenant/project/analysis data.

## Release topology

Semantic tags build one arm64-compatible SAM artifact. Staging and production deploy that same artifact. Lambda `AutoPublishAlias` creates immutable versions; CodeDeploy traffic shifting may be enabled after bootstrap. CloudWatch alias alarms and smoke checks protect promotion.

The release artifact also carries the committed SBOM and supply-chain checksum ledger.

## Deliberate boundaries

- Cognito authenticates users; tenant membership authorizes application actions.
- GitHub OIDC authenticates delivery workflows and is unrelated to application users.
- application audit events describe domain mutations; CloudTrail remains responsible for AWS control-plane audit.
- API Gateway provides distributed perimeter throttling; the Lambda process limiter is defense in depth.
- the M2 frontend remains outside M1.4 and must consume these identity/authorization contracts rather than reimplement authority client-side.
