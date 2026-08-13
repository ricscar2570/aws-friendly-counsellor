# CI/CD and release promotion — M1.4

## Continuous integration

Every push and pull request performs exact dependency installation, Python compilation, contract snapshot verification, environment/security invariant validation, supply-chain evidence verification, tests with a 90% coverage gate, SAM linting, an arm64-compatible containerized SAM build, and source-package layout verification.

## Dev delivery

A push to `main` can deploy the exact commit to dev. GitHub exchanges an OIDC token for temporary AWS credentials, CloudFormation deploys through its separate execution role, and public health/release smoke tests confirm the deployed artifact.

## Tagged release pipeline

A `vMAJOR.MINOR.PATCH` tag validates the full repository, builds one arm64 SAM artifact, records the exact Git SHA, bundles the committed SBOM/checksum evidence, deploys the same artifact to staging, runs smoke tests, waits for the production environment gate, and promotes the identical artifact to production.

Environment parameters change at deployment; application code and dependencies do not.

## Supply-chain controls

- checkout does not persist repository credentials;
- AWS credentials are temporary OIDC sessions;
- direct and transitive Python versions are exact pins;
- `supply-chain/sbom.cdx.json` records the version-resolved Python component inventory;
- `supply-chain/evidence.sha256` fingerprints lock files, workflow definitions, Python runtime intent, and the SBOM;
- CI fails when committed evidence is stale;
- release artifacts carry the evidence;
- Dependabot monitors Python and GitHub Actions versions;
- Lambda build occurs in the target architecture container;
- release identity contains both semantic version and exact Git SHA.

Package-artifact hash locking and GitHub Action commit-SHA pinning are desirable follow-up hardening and are not claimed by M1.4.
