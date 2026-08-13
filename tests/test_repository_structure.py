from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_monorepo_boundaries_are_present_and_flat_backend_is_removed():
    required = [
        ROOT / "apps/api/src/aws_friendly_counsellor",
        ROOT / "apps/web",
        ROOT / "packages/contracts/python/aws_friendly_counsellor_contracts",
        ROOT / "packages/contracts/openapi/v1/openapi.json",
        ROOT / "infra/sam/template.yaml",
        ROOT / "docs/DATA_MODEL.md",
        ROOT / "scripts/migrate_local_database.py",
        ROOT / "apps/api/requirements.in",
        ROOT / "apps/api/requirements.txt",
        ROOT / "requirements-dev.in",
        ROOT / "requirements-dev.txt",
        ROOT / ".python-version",
    ]
    assert all(path.exists() for path in required)
    assert not (ROOT / "backend").exists()
    assert not (ROOT / "template.yaml").exists()


def test_sam_template_uses_custom_builder_proxy_and_durable_dynamodb():
    template_path = ROOT / "infra/sam/template.yaml"
    document = yaml.compose(template_path.read_text(encoding="utf-8"))
    assert document is not None
    text = template_path.read_text(encoding="utf-8")
    assert "BuildMethod: makefile" in text
    assert "Handler: aws_friendly_counsellor.lambda_handler.handler" in text
    assert 'Path: "/{proxy+}"' in text
    assert "Method: ANY" in text
    assert "AllowOrigin: \"'*'\"" not in text
    assert "Type: AWS::DynamoDB::Table" in text
    assert "BillingMode: PAY_PER_REQUEST" in text
    assert "SSEEnabled: true" in text
    assert "PointInTimeRecoveryEnabled: true" in text
    assert "DeletionPolicy: Retain" in text
    assert "UpdateReplacePolicy: Retain" in text
    assert "STORAGE_BACKEND: dynamodb" in text
    assert "DYNAMODB_TABLE_NAME: !Ref ApplicationDataTable" in text


def test_lambda_policy_is_scoped_and_does_not_allow_scan_or_wildcard_dynamodb():
    text = (ROOT / "infra/sam/template.yaml").read_text(encoding="utf-8")
    assert "dynamodb:TransactWriteItems" in text
    assert "dynamodb:Query" in text
    assert "dynamodb:Scan" not in text
    assert "Resource: '*'" not in text
    assert "Resource: !GetAtt ApplicationDataTable.Arn" in text


def test_lambda_packaging_script_copies_only_runtime_packages():
    text = (ROOT / "scripts/package_lambda.sh").read_text(encoding="utf-8")
    assert "apps/api/src/aws_friendly_counsellor" in text
    assert "packages/contracts/python/aws_friendly_counsellor_contracts" in text
    assert 'cp -R "$ROOT_DIR/backend' not in text


def test_dependency_sets_are_fully_version_pinned():
    for relative in ("apps/api/requirements.txt", "requirements-dev.txt"):
        for raw_line in (ROOT / relative).read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("-r "):
                continue
            assert "==" in line, f"unversioned dependency in {relative}: {line}"
            assert not any(token in line for token in (">=", "<=", "~=", "!=", ">", "<"))


def test_sensitive_persistent_resources_are_retained():
    text = (ROOT / "infra/sam/template.yaml").read_text(encoding="utf-8")
    user_pool_block = text.split("  ApplicationUserPool:", 1)[1].split("  ApplicationUserPoolClient:", 1)[0]
    table_block = text.split("  ApplicationDataTable:", 1)[1].split("  AnalyzeFunction:", 1)[0]
    for block in (user_pool_block, table_block):
        assert "DeletionPolicy: Retain" in block
        assert "UpdateReplacePolicy: Retain" in block
