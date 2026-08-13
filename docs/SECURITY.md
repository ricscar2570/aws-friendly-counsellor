# Security model — M1.4

## Identity boundary

Deployed environments use Amazon Cognito user pools and an API Gateway Cognito authorizer. API Gateway validates the bearer token before protected proxy requests reach Lambda. The application consumes the verified `sub` claim exposed by the API Gateway authorizer through the Mangum AWS event.

The local/test identity shim exists only to make deterministic development and tests possible. Even if `ALLOW_LOCAL_IDENTITY=true` is injected accidentally, the shim refuses to activate when `APP_ENVIRONMENT` is `dev`, `staging`, or `production`.

The M1.3 API-key/Secrets Manager authentication mechanism has been removed from application runtime, SAM, and the CloudFormation execution-role permissions.

## Tenant authorization

`X-Tenant-ID` is a selector, not a credential. A request is authorized only when all of these are true:

1. the token supplies a valid authenticated subject;
2. the selected tenant exists and is active;
3. the subject has a durable active membership in that tenant;
4. the membership role meets the route requirement.

An unrelated authenticated subject receives a not-found response rather than confirmation that the selected tenant exists.

### Roles

| Role | Read tenant/projects/analysis | Create/update projects and analyses | Read audit / memberships | Manage memberships |
|---|---:|---:|---:|---:|
| `viewer` | yes | no | no | no |
| `editor` | yes | yes | no | no |
| `admin` | yes | yes | yes | editor/viewer only |
| `owner` | yes | yes | yes | all roles |

An owner cannot modify its own owner membership in M1.4. This conservative rule prevents accidental last-owner lockout; controlled ownership transfer is intentionally deferred until it can prove that another active owner exists.

## Cognito controls

- separate user pool per application environment;
- email username and verified email recovery;
- minimum 14-character password with upper/lowercase, numeric, and symbol requirements;
- optional software-token MFA capability;
- token revocation enabled on the app client;
- user-existence error suppression enabled;
- self-registration enabled only by the dev profile and disabled in staging/production;
- Cognito deletion protection enabled in production;
- retained user pools on stack deletion/replacement.

MFA is `OPTIONAL`, not mandatory. Production policy may raise this later; the current milestone provides the mechanism without claiming universal MFA enrollment.

## Durable audit

Tenant creation, membership creation/update, project creation/update, and analysis creation write audit events with actor subject, action, resource, request ID, timestamp, and bounded metadata. SQLite performs the business mutation and audit insert in one database transaction. DynamoDB uses `TransactWriteItems` for audited mutations.

Audit events are tenant-scoped and readable only by admin/owner roles. They are application audit evidence, not a substitute for CloudTrail or infrastructure audit logs.

## Delivery and infrastructure controls

- GitHub Actions obtains temporary AWS credentials through OIDC;
- OIDC trust is restricted to an exact repository/environment subject, with optional immutable repository-ID subject support;
- deployment and CloudFormation execution roles are separate;
- long-lived AWS access keys are absent from workflows;
- Lambda uses immutable versions behind the `live` alias;
- optional CodeDeploy traffic shifting can roll back on alias errors or throttles;
- failed CloudFormation changes use rollback;
- production DynamoDB deletion protection and retained data remain enabled;
- CORS forbids wildcard origins and the bearer `Authorization` header is explicitly allowed;
- protected API proxy routes use the Cognito authorizer while root, health checks, and CORS OPTIONS remain public;
- the Lambda DynamoDB policy allows targeted Get/Put/Update/Query/transaction operations and not Scan.

## Supply-chain evidence

M1.4 commits a deterministic CycloneDX SBOM for the exact version-resolved Python dependency sets plus a checksum ledger covering dependency locks, Python runtime intent, reviewed workflow definitions, and the SBOM. CI runs the evidence generator in `--check` mode, and release artifacts include both evidence files.

This is stronger evidence than M1.3 but is not a claim of full SLSA provenance: Python package artifact hashes and GitHub Action commit-SHA pinning remain further hardening opportunities.

## Residual risks

- no real AWS deployment, Cognito sign-in, or API Gateway authorizer execution was possible in this execution environment;
- optional MFA does not guarantee every account has MFA configured;
- the process-local application rate limiter is defense in depth only; distributed throttling remains API Gateway's responsibility;
- membership role changes are application-authorized but there is not yet a separate break-glass administrative control plane;
- CloudFormation execution remains privileged enough to create/update the stack resource types and must be isolated and reviewed;
- CloudTrail/SIEM retention, alert correlation, penetration testing, and formal privacy classification are later operational gates.

See `docs/THREAT_MODEL.md` for abuse cases and trust-boundary analysis.
