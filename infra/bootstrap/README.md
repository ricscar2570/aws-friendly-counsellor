# GitHub OIDC bootstrap

`github-oidc.yaml` creates:

- an optional GitHub OIDC provider;
- an encrypted, private, versioned SAM artifact bucket;
- a GitHub deployment role;
- a separate CloudFormation execution role.

Example first-environment deployment:

```bash
aws cloudformation deploy \
  --template-file infra/bootstrap/github-oidc.yaml \
  --stack-name awsfc-pipeline-dev \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    GitHubOwner=OWNER \
    GitHubRepository=REPOSITORY \
    GitHubEnvironment=dev
```

For staging and production in the same AWS account, pass the provider ARN output from the first stack as `ExistingOidcProviderArn`.

Copy the output role ARNs and bucket name into the matching GitHub environment variables. No AWS access key or secret access key is created.


## Immutable GitHub subject claims

For a repository using immutable owner/repository IDs, pass the exact `sub` claim reported by GitHub:

```bash
OidcSubjectClaim='repo:OWNER@OWNER_ID/REPOSITORY@REPOSITORY_ID:environment:dev'
```

Do not replace this with a wildcard. Deploy a separate bootstrap stack and role for each GitHub environment.
