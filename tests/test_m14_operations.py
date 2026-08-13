from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from aws_friendly_counsellor.core import config
from aws_friendly_counsellor.security import auth

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_configuration_rejects_invalid_environment_and_wildcard_cors(monkeypatch):
    monkeypatch.setenv("APP_ENVIRONMENT", "shared")
    with pytest.raises(RuntimeError, match="APP_ENVIRONMENT"):
        config.load_settings()

    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    monkeypatch.setenv("ALLOWED_ORIGINS", "*")
    with pytest.raises(RuntimeError, match="Wildcard"):
        config.load_settings()


def test_runtime_configuration_rejects_invalid_log_level(monkeypatch):
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://example.test")
    monkeypatch.setenv("LOG_LEVEL", "VERBOSE")
    with pytest.raises(RuntimeError, match="LOG_LEVEL"):
        config.load_settings()


def test_local_identity_never_activates_in_deployed_environments(monkeypatch):
    for environment in ("dev", "staging", "production"):
        monkeypatch.setenv("APP_ENVIRONMENT", environment)
        monkeypatch.setenv("ALLOW_LOCAL_IDENTITY", "true")
        assert auth._local_identity_enabled() is False


def test_rate_limit_rejects_non_positive_configuration(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "0")
    monkeypatch.setenv("RATE_LIMIT_WINDOW", "60")
    with pytest.raises(RuntimeError, match="positive"):
        auth.check_rate_limit("subject:test")


def test_cognito_environment_and_oidc_trust_are_present():
    sam = (ROOT / "infra/sam/template.yaml").read_text(encoding="utf-8")
    config_text = (ROOT / "infra/sam/samconfig.toml").read_text(encoding="utf-8")
    bootstrap = (ROOT / "infra/bootstrap/github-oidc.yaml").read_text(encoding="utf-8")
    assert yaml.compose(sam) is not None
    assert yaml.compose(bootstrap) is not None
    assert "StageName: !Ref EnvironmentName" in sam
    assert "AWS::Cognito::UserPool" in sam
    assert "AWS::Cognito::UserPoolClient" in sam
    assert "DefaultAuthorizer: CognitoAuthorizer" in sam
    assert "AddDefaultAuthorizerToCorsPreflight: false" in sam
    assert "MfaConfiguration: OPTIONAL" in sam
    assert "SOFTWARE_TOKEN_MFA" in sam
    assert "PreventUserExistenceErrors: ENABLED" in sam
    assert "API_KEY_SECRET_ARN" not in sam
    assert "VALID_API_KEYS" not in sam
    assert "AutoPublishAlias: live" in sam
    assert "DeploymentPreference:" in sam
    assert "DeletionProtectionEnabled" in sam
    assert all(
        f"[{environment}.global.parameters]" in config_text
        for environment in ("dev", "staging", "production")
    )
    assert "AllowSelfRegistration=true" in config_text
    assert config_text.count("AllowSelfRegistration=false") == 2
    assert "token.actions.githubusercontent.com:sub" in bootstrap
    assert "environment:${GitHubEnvironment}" in bootstrap
    assert "OidcSubjectClaim:" in bootstrap
    assert "HasCustomOidcSubjectClaim" in bootstrap
    assert "cognito-idp:CreateUserPool" in bootstrap
    assert "secretsmanager:" not in bootstrap


def test_deployment_workflows_use_oidc_and_never_long_lived_aws_keys():
    workflows = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / ".github/workflows").glob("*.yml"))
    )
    assert "id-token: write" in workflows
    assert "aws-actions/configure-aws-credentials@v6.2.3" in workflows
    assert "aws-actions/setup-sam@v3" in workflows
    assert "actions/checkout@v6.0.2" in workflows
    assert "actions/setup-python@v7.0.0" in workflows
    assert "actions/upload-artifact@v7.0.1" in workflows
    assert "actions/download-artifact@v8.0.1" in workflows
    assert "AWS_ACCESS_KEY_ID" not in workflows
    assert "aws-access-key-id" not in workflows
    deploy_script = (ROOT / "scripts/deploy_environment.sh").read_text(encoding="utf-8")
    assert "--on-failure ROLLBACK" in deploy_script
    assert "deploy_environment.sh" in workflows
    assert "smoke_test.py" in workflows
