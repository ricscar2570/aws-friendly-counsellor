# ADR 0004 — Managed identity, tenant membership, and audit

**Status:** Accepted for M1.4  
**Date:** 2026-08-13

## Context

M1.3 structurally isolated tenant data but authenticated callers with an application API key while accepting `X-Tenant-ID` as the tenant scope. That was appropriate only for controlled internal access: a valid key plus a known tenant ID was not a sufficient public SaaS authorization model.

## Decision

- Use an Amazon Cognito user pool per environment and an API Gateway Cognito authorizer for protected routes.
- Treat the verified Cognito `sub` as the application identity subject.
- Persist tenant membership and role in the application data store rather than using Cognito groups as tenant authority.
- Treat `X-Tenant-ID` strictly as a tenant selector.
- Support `viewer`, `editor`, `admin`, and `owner` roles with a fixed server-side permission hierarchy.
- Create the tenant creator's owner membership atomically with tenant provisioning.
- Persist application audit events for critical mutations in the same transaction as the mutation.
- Remove the M1.3 API-key/Secrets Manager authentication mechanism from deployable runtime and its obsolete IAM permissions.

## Consequences

### Positive

- one user can hold different roles in different tenants;
- tenant authority is evaluated on every request from durable state;
- suspended membership takes effect independently of token lifetime;
- cross-tenant selectors cannot grant access;
- mutation/audit split-brain is prevented for the covered domain operations;
- M2 can consume a stable server-side authorization model.

### Tradeoffs

- every tenant request adds membership persistence access;
- ownership transfer needs a later explicit last-owner invariant rather than permissive self-demotion;
- emergency rollback across M1.3/M1.4 must deploy the complete stack because the identity infrastructure changed;
- Cognito staging proof remains required because local tests cannot execute API Gateway token validation.
