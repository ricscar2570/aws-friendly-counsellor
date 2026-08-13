# M0 validation report

Date: 2026-07-29
Version: 3.1.0

## Completed checks

- Python source compilation completed successfully.
- 15 automated tests passed.
- Measured backend test coverage: 92%.
- End-to-end API checks passed for `/api/analyze`, `/api/iac`, and `/api/narrative`.
- A representative recommendation produced canonical service IDs and a non-empty, non-zero cost range.
- Anonymous access is denied by default.
- Request fields `budget`, `region`, and `advanced_guide` affect generated output.
- Terraform output connects API Gateway to Lambda and includes safe baselines for DynamoDB, S3, Cognito, and CloudWatch.
- `template.yaml` passed structural YAML parsing.
- Shell packaging script passed `bash -n` syntax validation.
- Python requirement declarations passed requirement-string parsing.
- No backup, broken, old, empty, or stale Lambda zip files remain in the source tree.
- A basic scan found no embedded demonstration key, AWS access-key pattern, or plaintext `aws_secret_access_key` assignment.

## Environment limitations

The execution environment did not provide the AWS SAM CLI, Terraform CLI, or an accessible Python package index. Therefore:

- `sam validate --lint`, `sam build`, and a real CloudFormation deployment were not executed;
- `terraform validate`, `terraform plan`, and an AWS apply were not executed;
- a fresh online dependency installation, including Mangum, could not be completed here.

The repository includes CI, dependency manifests, SAM configuration, and packaging instructions so these checks can run in a normal connected development or CI environment.

## Remaining product milestones

M0 consolidates the backend. It does not include the production frontend, live AWS pricing integration, a trained ML classifier, persistent distributed rate limiting, managed identity/authorizer integration, or workload-specific production Terraform for every recommended service.
