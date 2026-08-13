# ADR 0002 — Persistence adapters and immutable analysis history

- Status: accepted
- Date: 2026-08-01

## Context

M1.1 produced analysis responses without durable tenant or project state. M1.2 requires local persistence, deployable AWS persistence, hard tenant scoping, historical reproducibility, and protection from concurrent overwrites.

## Decision

Use one domain repository protocol with two adapters:

- SQLite for local development and deterministic tests;
- DynamoDB for AWS deployment.

Projects are mutable through optimistic revisions. Analysis history is append-only and stores complete normalized request and validated result snapshots. Version numbers are allocated transactionally per project.

DynamoDB uses a single-table key design optimized for the required access patterns. No generic scan endpoint is introduced.

## Consequences

Positive:

- HTTP handlers remain independent of storage technology;
- local development requires no external database;
- historical results remain reproducible;
- concurrent project updates cannot silently overwrite one another;
- tenant scope is mandatory in every repository access pattern.

Negative:

- two adapters must remain behaviorally equivalent;
- full DynamoDB integration testing requires LocalStack or an AWS test account;
- storing complete result snapshots increases storage consumption;
- API-key identity still cannot prove tenant membership until M1.4.

## Rejected alternatives

- storing data directly in route handlers: rejected because it couples transport and persistence;
- mutable analysis rows: rejected because history would cease to be auditable;
- PostgreSQL immediately: rejected because current access patterns do not justify operational overhead;
- in-memory persistence: rejected because it cannot satisfy durability or Lambda execution behavior.
