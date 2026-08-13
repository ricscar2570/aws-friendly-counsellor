from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/deploy_environment.sh"


def _fake_sam(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "sam.log"
    fake = bin_dir / "sam"
    fake.write_text(
        '#!/usr/bin/env bash\nprintf "%s\\n" "$*" >> "$SAM_TEST_LOG"\n'
        'if [[ "$1" == "build" ]]; then mkdir -p .aws-sam/build; touch .aws-sam/build/template.yaml; fi\n',
        encoding="utf-8",
    )
    fake.chmod(0o755)
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "SAM_TEST_LOG": str(log),
            "RELEASE_VERSION": "v3.5.0",
            "GIT_SHA": "a" * 40,
            "ALLOWED_ORIGINS": "https://example.test",
            "SAM_ARTIFACT_BUCKET": "artifact-bucket",
            "CLOUDFORMATION_EXECUTION_ROLE_ARN": "arn:aws:iam::123456789012:role/cfn",
        }
    )
    return log, env


def test_deploy_script_applies_complete_production_profile(tmp_path):
    log, env = _fake_sam(tmp_path)
    env["ENABLE_GRADUAL_DEPLOYMENT"] = "true"
    completed = subprocess.run(
        [str(SCRIPT), "production"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    commands = log.read_text(encoding="utf-8")
    assert "build --config-env production --use-container" in commands
    assert "EnvironmentName=production" in commands
    assert "LogRetentionDays=90" in commands
    assert "ReservedConcurrentExecutions=25" in commands
    assert "EnableContributorInsights=true" in commands
    assert "EnableTableDeletionProtection=true" in commands
    assert "AllowSelfRegistration=false" in commands
    assert "DeploymentPreferenceType=Canary10Percent10Minutes" in commands
    assert "--on-failure ROLLBACK" in commands



def test_rollback_forces_all_at_once_and_can_reuse_built_artifact(tmp_path):
    log, env = _fake_sam(tmp_path)
    build_dir = ROOT / "infra/sam/.aws-sam/build"
    build_dir.mkdir(parents=True, exist_ok=True)
    (build_dir / "template.yaml").write_text("placeholder", encoding="utf-8")
    env.update(
        {
            "SKIP_BUILD": "true",
            "FORCE_ALL_AT_ONCE": "true",
            "ENABLE_GRADUAL_DEPLOYMENT": "true",
        }
    )
    completed = subprocess.run(
        [str(SCRIPT), "dev"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    commands = log.read_text(encoding="utf-8")
    assert "build " not in commands
    assert "EnableGradualDeployment=false" in commands
    assert "DeploymentPreferenceType=AllAtOnce" in commands


def test_deploy_script_rejects_non_semantic_production_release(tmp_path):
    _, env = _fake_sam(tmp_path)
    env["RELEASE_VERSION"] = "main"
    completed = subprocess.run(
        [str(SCRIPT), "production"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode != 0
    assert "expected a semantic version tag" in completed.stderr
