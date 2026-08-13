# M1.4 validation report

**Milestone:** managed identity, tenant authorization, durable audit, threat model, and stronger supply-chain evidence  
**Application version:** `3.5.0-m1.4`  
**Contract version:** `1.3.0`  
**Validation date:** 2026-08-13

## Baseline integrity

M1.4 was built from the sealed `3.4.0-m1.3` archive rather than reconstructing M0/M1 from memory. Before modification the extracted M1.3 repository passed its full baseline suite: **61 tests passed**. The preserved M1.3 report recorded **94.45% line coverage** and the operational-delivery gate as complete, with managed identity explicitly deferred to M1.4.

## Scope completed

### Managed identity

- Amazon Cognito user pool and public app client are defined per environment;
- API Gateway uses a Cognito user-pool authorizer on protected proxy routes;
- root, health endpoints, and CORS preflight are explicit public exceptions;
- application identity is derived from verified API Gateway authorizer claims exposed through Mangum;
- the M1.3 API-key/Secrets Manager application-authentication path is removed;
- local/test debug identity is hard-disabled for `dev`, `staging`, and `production` even if its flag is set;
- the API exposes `GET /api/v1/me` for the authenticated subject.

### Tenant authorization

- durable membership model: `viewer`, `editor`, `admin`, `owner`;
- membership state: `active` or `suspended`;
- tenant creator becomes owner atomically with tenant creation;
- `X-Tenant-ID` is a selector only and cannot authorize a request;
- unrelated authenticated callers receive tenant not-found concealment;
- viewer/editor/admin/owner route thresholds are enforced server-side;
- admins can manage viewer/editor memberships but cannot grant or modify admin/owner roles;
- an active owner cannot change its own owner membership, preventing self-lockout;
- suspended membership is rejected on each tenant-scoped request.

### Durable audit

Critical tenant mutations now write audit events containing actor subject, action, resource, request ID, timestamp, and structured metadata.

Covered mutation classes:

- tenant creation;
- membership creation;
- membership update;
- project creation;
- project update;
- analysis creation.

SQLite persists the mutation and audit event inside one database transaction. DynamoDB uses `TransactWriteItems` for audited writes. Audit events are tenant-scoped and readable only by admin/owner roles.

### Persistence evolution

- SQLite schema ledger advanced additively to migration 2;
- membership and audit tables were added without rewriting existing tenant/project/analysis rows;
- DynamoDB adds `MEMBER#...` and `AUDIT#...` sort-key families while preserving all M1.2/M1.3 keys;
- project/analysis behavior and immutable analysis history remain compatible.

### Cognito hardening

The stack defines:

- 14-character minimum password complexity policy;
- optional software-token MFA capability;
- token revocation on the app client;
- user-existence error suppression;
- verified-email account recovery;
- dev-only self-registration;
- staging/production administrator-controlled account creation;
- production Cognito deletion protection;
- retained user pools on stack removal/replacement.

Optional MFA is not represented as universal MFA enrollment.

### Supply-chain evidence

- deterministic CycloneDX 1.5 SBOM generated from exact version-resolved Python dependency files;
- deterministic SHA-256 evidence ledger fingerprints dependency locks, Python runtime intent, GitHub workflow definitions, and the SBOM;
- CI quality gate checks evidence freshness;
- tagged release artifacts include the SBOM and checksum evidence;
- obsolete Secrets Manager permissions were removed from the CloudFormation execution role.

### Threat model

`docs/THREAT_MODEL.md` records assets, trust boundaries, abuse cases, mitigations, security-regression requirements, and residual risks covering public API identity, tenant authorization, persistence/audit, GitHub OIDC, and CloudFormation delivery.

## Validation results

The final local quality gate produced:

- **67 tests passed**;
- **91.91% total line coverage**;
- required coverage threshold: **90%**;
- Python compilation passed;
- OpenAPI and top-level JSON Schema snapshot check passed;
- environment/deployment invariant check passed;
- supply-chain evidence freshness check passed;
- SAM and bootstrap templates passed YAML node composition;
- `samconfig.toml` remained parseable through the environment validator;
- deploy/package shell scripts passed `bash -n`;
- role-boundary tests passed for outsider, viewer, editor, admin, owner, and suspended membership;
- DynamoDB unit tests passed for membership/audit primitives and transactional audit writes;
- existing planning, persistence, pagination, immutable-history, and delivery tests remained green.

## Definition of Done

| Requirement | Result |
|---|---|
| Managed user identity in deployable infrastructure | Pass structurally |
| Cognito-protected API proxy | Pass structurally |
| Public health/preflight exceptions explicit | Pass |
| Claim-derived application principal | Pass |
| Local identity impossible in deployed environments | Pass |
| Tenant membership source of truth | Pass |
| `X-Tenant-ID` cannot grant authority | Pass |
| Viewer/editor/admin/owner hierarchy | Pass |
| Role-management ceiling | Pass |
| Suspended membership enforcement | Pass |
| Atomic creator-owner provisioning | Pass |
| Durable audit model | Pass |
| Audit atomic with covered mutations | Pass in SQLite tests and DynamoDB unit structure |
| Cross-tenant concealment | Pass |
| Additive contract `1.3.0` | Pass |
| Contract snapshots synchronized | Pass |
| Threat model and abuse cases | Pass |
| SBOM and deterministic evidence | Pass |
| Coverage at least 90% | Pass — 91.91% |
| Real Cognito sign-in/API Gateway authorizer proof | Not executable here |
| Real DynamoDB cross-tenant integration proof | Not executable here |
| Real canary/alarm rollback exercise | Not executable here |
| Penetration test | Not executed |

## Validation limitations

This execution environment does not provide AWS SAM CLI, Docker, AWS credentials, or an AWS account. It also does not provide the repository's target Python 3.12 interpreter; local tests executed under Python 3.13.5 while `.python-version` and CI remain pinned to Python 3.12.

Therefore this report does **not** claim:

- `sam validate --lint` executed locally;
- containerized `sam build` executed locally;
- CloudFormation change-set validation against AWS;
- Cognito user provisioning/sign-in/token issuance;
- API Gateway rejection/acceptance of live Cognito tokens;
- live Lambda/DynamoDB transaction integration;
- CloudTrail evidence;
- real CodeDeploy canary rollback;
- external penetration or WAF/bot testing.

The repository's CI definitions retain those AWS-capable build and deployment gates. Local evidence covers application behavior, authorization, persistence contracts, infrastructure structure, generated contracts, release configuration, and supply-chain snapshots.

## Residual risks

1. MFA is available but optional; production policy can require stronger enrollment later.
2. Public self-service tenant provisioning is not ready: production self-registration is intentionally disabled and future signup must add entitlement/quota/abuse controls.
3. The CloudFormation execution role remains necessarily powerful for the resource types it manages; use account/organization boundaries and workflow review.
4. Python package artifact hashes are not yet pinned and GitHub Actions use reviewed release tags rather than immutable commit SHAs.
5. Application audit events are not CloudTrail and do not replace control-plane/SIEM evidence.
6. Emergency downgrade to M1.3 changes the identity security posture and must redeploy the complete M1.3 stack, not only Lambda code.

## Next gate

The correct next step is an **M1.5 staging/security proof gate**, not frontend implementation. It should execute the already-defined M1.4 system in a real AWS environment and prove:

- Cognito account creation/sign-in and token acquisition;
- protected/public API Gateway route behavior;
- live tenant role and cross-tenant isolation against DynamoDB;
- audit persistence and CloudTrail correlation;
- first/second gradual deployment behavior and alarm rollback;
- backup/restore and retained-resource procedures;
- external security regression checks;
- Python 3.12 clean install/SAM arm64 build evidence.

M2 should begin only after this real-environment gate is sealed.
