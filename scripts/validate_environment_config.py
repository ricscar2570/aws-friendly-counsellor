from __future__ import annotations

import re
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ENVIRONMENTS = ("dev", "staging", "production")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    template_path = ROOT / "infra/sam/template.yaml"
    template = template_path.read_text(encoding="utf-8")
    _require(yaml.compose(template) is not None, "SAM template is not valid YAML")
    _require("StageName: !Ref EnvironmentName" in template, "API stage is not environment-scoped")
    _require("AWSFriendlyCounsellor-${EnvironmentName}-Analyzer" in template, "Lambda name is not environment-scoped")
    _require("VALID_API_KEYS" not in template and "API_KEY_SECRET_ARN" not in template, "Legacy API-key authentication remains in CloudFormation")
    _require("AWS::Cognito::UserPool" in template, "Cognito user pool is missing")
    _require("AWS::Cognito::UserPoolClient" in template, "Cognito app client is missing")
    _require("DefaultAuthorizer: CognitoAuthorizer" in template, "Cognito API authorizer is missing")
    _require("AddDefaultAuthorizerToCorsPreflight: false" in template, "CORS preflight must remain unauthenticated")
    _require("AutoPublishAlias: live" in template, "Lambda alias publishing is missing")
    _require("DeploymentPreference:" in template, "Gradual deployment configuration is missing")
    _require("PointInTimeRecoveryEnabled: true" in template, "DynamoDB PITR is missing")

    config = tomllib.loads((ROOT / "infra/sam/samconfig.toml").read_text(encoding="utf-8"))
    for environment in ENVIRONMENTS:
        _require(environment in config, f"samconfig is missing {environment}")
        stack_name = config[environment]["global"]["parameters"]["stack_name"]
        _require(stack_name.endswith(environment), f"{environment} stack name is not isolated")
        overrides = config[environment]["deploy"]["parameters"]["parameter_overrides"]
        _require(f"EnvironmentName={environment}" in overrides, f"{environment} parameter override mismatch")
        expected_registration = "true" if environment == "dev" else "false"
        _require(f"AllowSelfRegistration={expected_registration}" in overrides, f"{environment} self-registration policy mismatch")

    workflows = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted((ROOT / ".github/workflows").glob("*.yml"))
    )
    _require("id-token: write" in workflows, "Deployment workflows do not request OIDC tokens")
    _require("configure-aws-credentials@v6.2.3" in workflows, "Pinned AWS OIDC credential action is missing")
    _require("setup-sam@v3" in workflows, "Current AWS SAM setup action is missing")
    _require("actions/checkout@v6.0.2" in workflows, "Checkout action is not pinned to the reviewed release")
    _require("actions/setup-python@v7.0.0" in workflows, "Python setup action is not pinned to the reviewed release")
    _require("actions/upload-artifact@v7.0.1" in workflows, "Artifact upload action is not pinned to the reviewed release")
    _require("actions/download-artifact@v8.0.1" in workflows, "Artifact download action is not pinned to the reviewed release")
    _require(not re.search(r"aws-access-key-id|AWS_ACCESS_KEY_ID", workflows, re.I), "Long-lived AWS credentials are referenced")
    bootstrap = (ROOT / "infra/bootstrap/github-oidc.yaml").read_text(encoding="utf-8")
    _require("OidcSubjectClaim:" in bootstrap, "Immutable GitHub OIDC subject support is missing")
    _require("HasCustomOidcSubjectClaim" in bootstrap, "OIDC subject selection condition is missing")
    _require("cognito-idp:CreateUserPool" in bootstrap, "CloudFormation role cannot create Cognito resources")
    _require("secretsmanager:" not in bootstrap, "Obsolete Secrets Manager permissions remain in the M1.4 bootstrap role")

    for requirements_path in (ROOT / "apps/api/requirements.txt", ROOT / "requirements-dev.txt"):
        for raw_line in requirements_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("-r "):
                continue
            _require("==" in line, f"Unpinned dependency in {requirements_path.relative_to(ROOT)}: {line}")
            _require(not any(token in line for token in (">=", "<=", "~=", "!=", ">", "<")), f"Dependency range in {requirements_path.relative_to(ROOT)}: {line}")

    deploy_script = (ROOT / "scripts/deploy_environment.sh").read_text(encoding="utf-8")
    _require("--on-failure ROLLBACK" in deploy_script, "CloudFormation rollback is not enforced")
    _require("deploy_environment.sh" in workflows, "Workflows bypass the controlled deployment script")
    print("Environment and deployment configuration is internally consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
