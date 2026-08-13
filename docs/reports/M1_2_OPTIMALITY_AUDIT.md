# M1.2 optimality audit before M1.3

**Audit date:** 2026-08-01  
**Input baseline:** AWS Friendly Counsellor `3.3.0-m1.2`  
**Decision:** suitable and internally coherent as the application baseline for M1.3, but not operationally optimal for deployment before the corrections recorded below.

## Executive verdict

M1.2 was not rebuilt or discarded. Its core design was sound:

- tenant scope was enforced by persistence interfaces and keys;
- project revisions used optimistic concurrency;
- analysis versions were immutable and sequential;
- SQLite and DynamoDB implemented the same repository contract;
- public contracts were generated from Pydantic models;
- the test and coverage gates were healthy;
- the monorepo boundaries established in M1.1 remained clean.

The baseline was therefore **optimal for continued development**, but **not yet optimal for controlled AWS promotion**. The operational gaps belonged precisely to M1.3 and were corrected there rather than hidden or deferred.

## Audit matrix

| Area | M1.2 result | Finding | M1.3 disposition |
|---|---|---|---|
| Domain and API structure | Pass | Modular monolith and v1 contracts remained coherent | Preserved |
| Tenant data isolation | Pass with boundary warning | Storage was tenant-scoped, but caller identity was still an API key plus `X-Tenant-ID` | Preserved; public exposure remains blocked until M1.4 |
| Persistence durability | Pass | SQLite restart persistence and DynamoDB transaction model were covered | Preserved and environment-isolated |
| Immutable history | Pass | Analysis snapshots and version allocation were correct | Preserved |
| Automated testing | Pass | 46 tests and 94.68% coverage at the M1.2 gate | Expanded in M1.3 |
| Environment isolation | Fail | Stack, API stage, Lambda, secret, logs, alarms, and table controls were not fully environment-profiled | Corrected |
| Secret handling | Fail | Static/demo key paths were unsuitable for a controlled AWS deployment | Replaced by retained Secrets Manager material and fail-closed retrieval |
| Release identity | Fail | Runtime could not prove environment, release, and Git revision | Added to health responses and headers |
| Release safety | Fail | No alias promotion, traffic shifting, alarm rollback, smoke gate, or explicit rollback workflow | Corrected |
| CI/CD trust | Fail | No OIDC promotion model or separation of deployment and execution roles | Corrected |
| Artifact architecture | Fail | An arm64 Lambda could be built on x86 with incompatible native wheels | Containerized architecture-matched SAM build required |
| Dependency resolution | Partial | Top-level pins did not fully resolve transitive versions | Complete version-resolved runtime and development sets added |
| Workflow supply chain | Partial | Core actions used moving major tags | Reviewed release versions pinned; Dependabot retained |
| Current GitHub OIDC claims | Partial | Only the historical repository-name subject format was accepted | Exact optional immutable owner/repository ID subject added |
| API Gateway logging prerequisite | Risk | REST execution logging would require an account/Region-level role not owned by an environment stack | Hidden prerequisite removed; metrics, X-Ray, and JSON Lambda logs retained |
| AWS deployment proof | Not available | No SAM CLI, Docker daemon, AWS account, or usable package index in the execution environment | CI definitions added; limitation remains explicit |

## Corrections required before M1.3 could be called complete

1. Isolate every deployable environment and its operational settings.
2. Centralize all parameter application in one deployment script.
3. Store application keys in Secrets Manager and fail closed when unavailable.
4. Publish immutable Lambda versions behind a `live` alias.
5. Add gradual promotion, automatic alarm rollback, and explicit rollback operations.
6. Use GitHub OIDC temporary credentials with exact subject restrictions.
7. Separate the GitHub deployment role from the CloudFormation execution role.
8. Build Python dependencies for the Lambda target architecture.
9. Pin direct and transitive dependency versions and reviewed workflow releases.
10. Expose liveness, readiness, environment, release, and Git metadata.
11. Prove the delivered ZIP again after extraction.

## Residual boundary deliberately left for M1.4

M1.2 and M1.3 do not bind `X-Tenant-ID` to a managed user membership claim. This is not an accidental defect: M1.4 is the identity, authorization, audit, and threat-model milestone. Until M1.4 is complete, the application is appropriate for controlled internal or pilot access only, not public multi-tenant SaaS exposure.

## Audit conclusion

The point reached after M1.2 was **technically sound and worth preserving**. Proceeding directly without an operational audit would not have been optimal. After applying the M1.3 corrections, the repository is now at the correct quality gate for the next step.
