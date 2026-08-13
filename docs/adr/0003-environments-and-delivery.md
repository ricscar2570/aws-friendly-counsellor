# ADR 0003 — Isolated environments and controlled delivery

## Status

Accepted for M1.3.

## Context

M1.2 had a deployable SAM template but used fixed resource names, a fixed API stage, parameter-based API keys, one CI workflow, and no controlled promotion or rollback path. Building arm64 Lambda dependencies directly on x86 runners could also produce incompatible native wheels.

## Decision

- use independent dev, staging, and production CloudFormation stacks;
- make environment and release identity runtime metadata;
- store generated API keys in Secrets Manager;
- authenticate GitHub to AWS through repository- and environment-scoped OIDC trust;
- separate GitHub deployment and CloudFormation execution roles;
- build Lambda dependencies in an arm64 SAM container;
- publish immutable Lambda versions behind a `live` alias;
- support CodeDeploy canary traffic shifting after first bootstrap;
- build tagged releases once and promote the same artifact;
- enforce automatic and manual rollback plus post-deployment smoke tests;
- keep all non-secret environment settings in version control.

## Consequences

Delivery is safer and auditable, but bootstrap configuration is more involved. The first deployment of each environment must disable gradual traffic shifting. GitHub environment protection becomes part of the production security boundary.
