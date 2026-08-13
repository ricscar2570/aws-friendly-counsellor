# Data model — M1.4

## Tenant

| Field | Meaning |
|---|---|
| `id` | Opaque immutable tenant identifier |
| `name` | Display name |
| `slug` | Unique normalized provisioning label |
| `status` | `active` or `suspended` |
| `revision` | Mutable-record revision |
| `created_at`, `updated_at` | UTC ISO-8601 timestamps |

Creating a tenant also creates an active `owner` membership for the authenticated creator in the same persistence transaction.

## Membership

| Field | Meaning |
|---|---|
| `tenant_id` | Tenant boundary |
| `subject` | Cognito `sub` / stable authenticated subject |
| `role` | `viewer`, `editor`, `admin`, or `owner` |
| `status` | `active` or `suspended` |
| `revision` | Optimistic-concurrency token |
| `created_at`, `updated_at` | UTC ISO-8601 timestamps |

Membership is the authorization source of truth. `X-Tenant-ID` never grants membership.

## Project

| Field | Meaning |
|---|---|
| `id` | Opaque immutable project identifier |
| `tenant_id` | Mandatory tenant owner |
| `name`, `description` | User-facing project definition |
| `estimated_users` | Monthly active-user planning input |
| `budget` | `low`, `medium`, or `high` |
| `region` | Supported AWS commercial region |
| `status` | `draft`, `active`, or `archived` |
| `revision` | Optimistic-concurrency token |
| `created_at`, `updated_at` | UTC ISO-8601 timestamps |

## Analysis version

| Field | Meaning |
|---|---|
| `analysis_id` | Opaque global identifier |
| `tenant_id`, `project_id` | Immutable ownership and parent relation |
| `version` | Monotonic integer within one project |
| `request` | Full normalized analysis request snapshot |
| `result` | Full validated analysis response snapshot |
| `created_at` | Immutable creation timestamp |

Analysis versions are append-only.

## Audit event

| Field | Meaning |
|---|---|
| `id` | Opaque audit identifier |
| `tenant_id` | Tenant boundary |
| `actor_subject` | Authenticated subject that caused the mutation |
| `action` | Stable action name such as `project.updated` |
| `resource_type`, `resource_id` | Mutated domain resource |
| `request_id` | Correlation identifier propagated through the API |
| `occurred_at` | UTC ISO-8601 timestamp |
| `metadata` | Small structured context that must not contain secrets |

## Invariants

1. Every project belongs to exactly one tenant.
2. Every analysis version belongs to the same tenant as its project.
3. Every membership belongs to exactly one tenant and subject pair.
4. Tenant selection never substitutes for membership authorization.
5. Tenant creation and creator-owner membership are atomic.
6. Membership/project updates require the expected revision.
7. Analysis version numbers never repeat within one project.
8. Archived projects cannot receive new analyses.
9. Audited mutations write domain state and audit evidence in one transactional boundary.
10. Historical analysis and audit events are not recalculated when mutable resources change.
