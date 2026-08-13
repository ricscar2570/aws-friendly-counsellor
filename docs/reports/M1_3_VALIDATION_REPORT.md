# M1.3 validation report

**Milestone:** environments, infrastructure, CI/CD, promotion, and rollback  
**Application version:** `3.4.0-m1.3`  
**Contract version:** `1.2.0`  
**Validation date:** 2026-08-01

## Scope completed

M1.3 converts the M1.2 application baseline into an environment-aware delivery system without changing the domain model or prematurely introducing public identity.

### Environment isolation

- separate `dev`, `staging`, and `production` CloudFormation stacks;
- environment-specific API Gateway stages and API names;
- environment-specific Lambda names, log retention, concurrency, alarms, secret, and table controls;
- complete non-secret profiles under `infra/sam/environments`;
- one canonical deployment script that always applies the full profile;
- protection against anonymous access outside dev;
- production DynamoDB deletion protection and retention;
- retained API-key secret and retained DynamoDB data.

### Runtime operations

- `/health/live` performs process-only liveness;
- `/health/ready` verifies the persistence backend;
- `/health` remains as the combined compatibility endpoint;
- responses expose environment and release headers;
- health payloads include release identifier and Git SHA;
- Lambda emits JSON logs and uses X-Ray tracing;
- API Gateway metrics and X-Ray remain enabled without introducing an undeclared account-wide logging-role prerequisite.

### Secret management

- CloudFormation creates a generated Secrets Manager key;
- Lambda receives only the secret ARN;
- secret values are cached briefly and never logged;
- comparison is constant-time;
- internal rate-limit principals are hash-derived rather than raw keys;
- Secrets Manager failures fail closed;
- a short failure cache prevents repeated service pressure;
- local `VALID_API_KEYS` support is retained only for development/testing.

### Build and dependency integrity

- Lambda architecture is `arm64`;
- SAM builds are containerized for architecture compatibility;
- standalone packaging selects the target manylinux platform explicitly;
- direct dependency intent is separated into `.in` files;
- runtime and development transitive versions are fully resolved in committed requirement files;
- CI executes `pip check` in its clean environment;
- Python runtime intent is recorded in `.python-version`;
- reviewed core workflow actions use explicit release versions;
- Dependabot monitors Python and GitHub Actions updates.

### Promotion and rollback

- Lambda versions are published behind a `live` alias;
- optional CodeDeploy canary/linear traffic shifting is configured;
- alias errors and throttles can trigger automatic deployment rollback;
- API Gateway 5xx has a separate operational alarm;
- CloudFormation deployment failure uses rollback rather than leaving a failed update in place;
- first gradual deployment is documented as a two-stage operation;
- a semantic-version tag pipeline builds one artifact and promotes that same artifact through staging and production;
- GitHub environments provide the approval boundary;
- smoke tests verify liveness, readiness, target environment, and exact release;
- manual promotion and known-good rollback workflows are included;
- release references and Git metadata are validated.

### AWS/GitHub trust bootstrap

- GitHub uses OIDC instead of stored AWS access keys;
- trust is restricted by audience and exact subject;
- both repository-name and current immutable owner/repository ID subject formats are supported;
- each GitHub environment has a distinct role trust boundary;
- deployment and CloudFormation execution roles are separate;
- the artifact bucket is private, encrypted, versioned, retained, and lifecycle-managed.

## Validation results

The final pre-archive validation produced:

- **61 tests passed**;
- **94.45% total line coverage**;
- required threshold: **90%**;
- Python compilation passed;
- OpenAPI and JSON Schema snapshot check passed;
- environment/deployment invariant check passed;
- all shell scripts passed `bash -n`;
- workflow YAML structure passed parsing;
- SAM and bootstrap CloudFormation YAML node composition passed;
- `samconfig.toml` passed TOML parsing;
- deployment profile behavior passed isolated fake-SAM tests;
- production semantic release enforcement passed;
- source-only Lambda package layout passed;
- an extracted source runtime passed isolated liveness and readiness smoke tests;
- no legacy backend directory, backup residue, or static application key was found.

The test count may increase during the final archive proof. The final response and archive proof section record the sealed values.

## Definition of Done

| Requirement | Result |
|---|---|
| Three isolated environment profiles | Pass |
| No static AWS credentials in workflows | Pass |
| No application secret value in CloudFormation/workflows | Pass |
| Temporary GitHub OIDC credentials | Pass |
| Exact OIDC subject restriction | Pass |
| Immutable-ID subject compatibility | Pass |
| Architecture-correct Lambda build path | Pass |
| Controlled canonical deploy script | Pass |
| Automatic failed-stack rollback | Pass |
| Alias and gradual deployment configuration | Pass |
| CloudWatch rollback alarms | Pass |
| Build-once staging-to-production path | Pass |
| Explicit known-good rollback path | Pass |
| Liveness/readiness/release smoke checks | Pass |
| Version-resolved dependency sets | Pass |
| Contracts synchronized | Pass |
| Coverage at least 90% | Pass |
| Public SaaS identity binding | Deferred to M1.4 by scope |
| Real AWS deployment proof | Not executable in this environment |

## Limitations and honest qualification

This environment does not provide AWS SAM CLI, Docker, AWS credentials, or access to an AWS account. Its package index also returned no distribution for the first pinned runtime package (`annotated-doc==0.0.4`), so a complete native-wheel Lambda ZIP could not be downloaded and assembled here.

Consequently, the following were **not** claimed:

- a real `sam validate --lint` execution in this environment;
- a real containerized `sam build` execution;
- a CloudFormation change-set preview against AWS;
- an actual canary deployment or alarm-induced rollback;
- a live DynamoDB/Secrets Manager/API Gateway integration test;
- a penetration test or public multi-tenant security approval.

The repository makes those checks mandatory in GitHub CI/CD where SAM, Docker, package resolution, OIDC, and AWS are available. Locally, application behavior, contracts, configuration invariants, scripts, package layout, and the sealed archive are independently verified.

## Residual risks

1. `X-Tenant-ID` is not yet derived from a managed identity claim. M1.4 must fix this before public SaaS access.
2. The CloudFormation execution role is intentionally privileged enough to manage the stack resource types. Production should use a dedicated AWS account or strong organizational boundary and protect workflow changes.
3. Dependency versions are pinned but not yet accompanied by package hashes or an SBOM. These are recommended M1.4 supply-chain additions.
4. API-key rotation remains an administrative sequence; managed user identity will supersede this pilot mechanism.
5. API Gateway execution logging is intentionally not enabled by environment stacks because it requires an account/Region-level role. Metrics, X-Ray, and JSON Lambda logs are active; centralized account logging can be added separately.

## Next milestone gate

M1.4 may begin only from this sealed M1.3 repository. Its scope is:

- Cognito or equivalent managed identity;
- tenant membership and role authorization;
- claim-derived tenant context;
- durable audit events;
- threat model and abuse cases;
- authorization and security regression tests;
- stronger supply-chain evidence.
