# M1.4 threat model and abuse cases

## Scope

This model covers the public API, Cognito/API Gateway identity boundary, Lambda/FastAPI authorization, tenant persistence, audit trail, and GitHub-to-AWS delivery path. It does not claim to cover the future M2 browser application, customer billing, or organization-wide AWS governance.

## Assets

- customer tenant/project/analysis data;
- tenant membership and role state;
- Cognito identities and tokens;
- durable audit events;
- release artifacts and source integrity;
- AWS deployment roles and production infrastructure.

## Trust boundaries

1. **Internet → API Gateway/Cognito**: untrusted clients present tokens and request data.
2. **API Gateway → Lambda**: application trusts authorizer claims only after gateway validation.
3. **Lambda → persistence**: application code must apply tenant keys and transactional invariants.
4. **GitHub Actions → AWS**: workflows exchange OIDC identity for temporary deployment credentials.
5. **CloudFormation execution role → resources**: privileged stack mutation boundary.

## Abuse-case matrix

| Abuse case | Primary control | Residual risk |
|---|---|---|
| Forge/omit bearer token | API Gateway Cognito authorizer; application fail-closed identity extraction | real gateway execution still needs staging proof |
| Supply another tenant's ID | membership lookup by verified subject; unrelated users receive not-found | compromised authorized account can access its legitimate tenants |
| Viewer attempts write | server-side role threshold | endpoint coverage must remain regression-tested |
| Admin grants itself/another admin or owner | role-management ceiling | owner account compromise remains high impact |
| Suspend a user but reuse an old token | membership status checked on every tenant request | non-tenant planning endpoints remain authenticated but not membership-bound by design |
| Delete/alter history to hide a change | analysis is immutable; no audit update/delete endpoint; retained persistence | sufficiently privileged direct AWS data access can bypass application controls |
| Mutation succeeds but audit write fails | SQLite transaction / DynamoDB transaction | future asynchronous side effects need separate outbox/saga design |
| Enumerate tenant IDs | opaque IDs plus concealment on missing membership | timing differences are not formally side-channel tested |
| Abuse local debug identity in production | hard environment gate refuses shim outside local/test | configuration code must remain covered by regression tests |
| Credential stuffing | Cognito user-existence suppression, password policy, optional TOTP MFA | MFA is optional; WAF/bot controls are not yet part of this stack |
| Authenticated user creates excessive tenants | production self-registration is disabled; process/perimeter throttles bound requests | public self-service provisioning will require entitlement/quota controls before signup is opened |
| Replay/reuse stolen token | short token validity and Cognito token revocation capability | API Gateway cannot infer compromise until token revocation/expiry semantics take effect |
| Malicious dependency/workflow drift | exact Python version pins, evidence snapshots, Dependabot, reviewed action refs | package hashes and immutable action commit SHAs are not yet enforced |
| GitHub credential theft | OIDC temporary credentials, exact subject trust, environment boundary | malicious reviewed workflow changes can still assume approved roles |
| Destructive stack update | CloudFormation rollback, retention, production deletion protection | execution role remains powerful; account-level guardrails are external |

## Security regression requirements

M1.4 cannot pass if tests fail to prove:

- outsider + valid tenant selector is denied;
- viewer cannot mutate;
- editor cannot administer memberships;
- admin cannot create/manage owner/admin memberships;
- suspended membership is denied;
- creator receives owner membership;
- audited mutations create durable audit events;
- local debug identity cannot activate in deployed environments;
- Cognito authorizer exists in the SAM template and public health/preflight routes are explicit exceptions;
- legacy API-key/Secrets Manager authentication is absent from deployable application infrastructure.

## Residual-risk acceptance for M1.4

The milestone is an implementation and local-validation gate, not a production accreditation. Before public launch, real AWS staging evidence must include Cognito sign-in, protected-route 401/403 behavior, cross-tenant tests against DynamoDB, CloudTrail review, canary/rollback exercise, and security testing from outside the AWS account.
