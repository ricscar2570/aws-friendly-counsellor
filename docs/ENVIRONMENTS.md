# Environment model — M1.4

## Profiles

| Setting | dev | staging | production |
|---|---:|---:|---:|
| Cognito self-registration | on | off | off |
| Log level | DEBUG | INFO | INFO |
| Log retention | 14 days | 30 days | 90 days |
| Reserved concurrency | 5 | 10 | 25 |
| Deployment strategy | All at once | 10% / 5 min canary | 10% / 10 min canary |
| Contributor Insights | off | off | on |
| DynamoDB deletion protection | off | off | on |
| Cognito deletion protection | off | off | on |

The authoritative non-secret profiles live under `infra/sam/environments`. `scripts/deploy_environment.sh` loads exactly one profile and supplies the complete parameter set.

## Identity isolation

Every stack creates a separate Cognito user pool and app client. User identities are therefore environment-local. Staging users do not become production users through release promotion, and application membership rows remain local to the environment's DynamoDB table.

The user pool is retained on stack deletion/replacement. Production additionally enables Cognito deletion protection.

## Required GitHub environment variables

Create GitHub environments named `dev`, `staging`, and `production` with:

- `AWS_REGION`;
- `AWS_DEPLOY_ROLE_ARN`;
- `CLOUDFORMATION_EXECUTION_ROLE_ARN`;
- `SAM_ARTIFACT_BUCKET`;
- `ALLOWED_ORIGINS`;
- `ENABLE_GRADUAL_DEPLOYMENT`.

Set `ENABLE_GRADUAL_DEPLOYMENT=false` on the first deployment of an environment. Production should require reviewers and protected semantic-version tags.

## Bootstrap

Deploy `infra/bootstrap/github-oidc.yaml` once per environment. The bootstrap role grants CloudFormation the resource-lifecycle permissions needed by Lambda, API Gateway, DynamoDB, Cognito, logs, alarms, CodeDeploy, IAM, and the artifact bucket. The obsolete M1.3 Secrets Manager application-key permissions have been removed.

If the repository uses GitHub immutable subject claims, pass the exact subject through `OidcSubjectClaim`; the trust policy uses exact equality rather than a wildcard.

## Decommissioning

DynamoDB data and Cognito user pools are retained. Decommissioning therefore requires an explicit retention/deletion decision rather than assuming stack deletion erases customer data or identities.
