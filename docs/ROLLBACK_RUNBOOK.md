# Rollback runbook — M1.4

## Automatic rollback

Two independent controls apply:

1. CloudFormation receives `--on-failure ROLLBACK` for stack failures.
2. When gradual deployment is enabled, CodeDeploy monitors live-alias errors and throttles and restores traffic to the previous Lambda version if an alarm breaches.

CodeDeploy rollback only changes Lambda traffic. It does not undo Cognito, API Gateway authorizer, DynamoDB, or other CloudFormation changes.

## Manual rollback

Use the `Roll back release` GitHub workflow for a known-good semantic tag or full commit SHA. The workflow validates the selected source, deploys its complete stack definition with all-at-once traffic restoration, and verifies public release/liveness/readiness metadata.

For a rollback across the M1.3 → M1.4 identity boundary, redeploy the **complete known-good stack**, not only a Lambda version. M1.3 code expects its old API-key infrastructure, while M1.4 code expects Cognito authorizer claims and membership state.

## Data compatibility

M1.4's SQLite migration 2 is additive: it creates membership and audit tables and does not rewrite existing tenant/project/analysis rows. DynamoDB adds `MEMBER#...` and `AUDIT#...` items without changing existing keys.

A rollback to M1.3 code can ignore these additional records, but M1.3 does not enforce M1.4 membership authorization. Such a rollback is therefore an emergency operational downgrade and must not be treated as equivalent security posture.

Cognito user pools and DynamoDB data use retention policies. A stack rollback/removal must not assume identity or customer data is deleted.

## Failed rollback

If rollback fails:

- inspect CloudFormation stack events and CodeDeploy state;
- do not delete the retained DynamoDB table or Cognito user pool as a troubleshooting shortcut;
- disable new deployments to the affected GitHub environment;
- restore the last successful complete stack revision through an authorized AWS operator;
- verify the API authorizer, `/health/ready`, release identity, and tenant authorization before reopening traffic;
- record the incident, exact Git SHA/tag, stack events, and any identity-policy downgrade.
