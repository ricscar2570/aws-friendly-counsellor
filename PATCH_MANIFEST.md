# AWS Friendly Counsellor — M1.4 v3.5.0 patch manifest

- Base repository: `aws-friendly-counsellor-m1.3-v3.4.0`
- Target: `3.5.0-m1.4`
- Public contract: `1.3.0`
- Validation: **67 tests passed; 91.91% total line coverage**
- Patch contents: only new/modified project files plus this operational manifest.

## Apply

1. Start from the sealed M1.3 v3.4.0 repository.
2. Copy the patch contents over the repository root, overwriting matching paths.
3. Delete every path listed under **Files to delete**.
4. Run `make validate` in a Python 3.12 environment.
5. Run the M1.5 real-AWS staging/security proof before claiming deployment validation.

## Files to delete

- `tests/test_m13_operations.py`

## New or modified project files (59)

- `.env.example`
- `.github/workflows/release-pipeline.yml`
- `CHANGELOG.md`
- `FILE_MANIFEST.sha256`
- `Makefile`
- `README.md`
- `apps/api/src/aws_friendly_counsellor/api/v1/common.py`
- `apps/api/src/aws_friendly_counsellor/api/v1/resources.py`
- `apps/api/src/aws_friendly_counsellor/core/config.py`
- `apps/api/src/aws_friendly_counsellor/domain/entities.py`
- `apps/api/src/aws_friendly_counsellor/domain/repositories.py`
- `apps/api/src/aws_friendly_counsellor/infrastructure/persistence/dynamodb_store.py`
- `apps/api/src/aws_friendly_counsellor/infrastructure/persistence/sqlite_store.py`
- `apps/api/src/aws_friendly_counsellor/main.py`
- `apps/api/src/aws_friendly_counsellor/security/auth.py`
- `apps/api/src/aws_friendly_counsellor/security/authorization.py`
- `docs/API_VERSIONING.md`
- `docs/ARCHITECTURE.md`
- `docs/CI_CD.md`
- `docs/DATA_MODEL.md`
- `docs/ENVIRONMENTS.md`
- `docs/IDENTITY_AUTHORIZATION.md`
- `docs/ROLLBACK_RUNBOOK.md`
- `docs/SECURITY.md`
- `docs/THREAT_MODEL.md`
- `docs/adr/0004-managed-identity-membership-audit.md`
- `docs/reports/M1_4_VALIDATION_REPORT.md`
- `infra/bootstrap/github-oidc.yaml`
- `infra/sam/environments/dev.env`
- `infra/sam/environments/production.env`
- `infra/sam/environments/staging.env`
- `infra/sam/samconfig.toml`
- `infra/sam/template.yaml`
- `packages/contracts/CHANGELOG.md`
- `packages/contracts/README.md`
- `packages/contracts/jsonschema/v1/AuditEventListResponse.schema.json`
- `packages/contracts/jsonschema/v1/IdentityResponse.schema.json`
- `packages/contracts/jsonschema/v1/TenantMembershipCreateRequest.schema.json`
- `packages/contracts/jsonschema/v1/TenantMembershipListResponse.schema.json`
- `packages/contracts/jsonschema/v1/TenantMembershipResponse.schema.json`
- `packages/contracts/jsonschema/v1/TenantMembershipUpdateRequest.schema.json`
- `packages/contracts/openapi/v1/openapi.json`
- `packages/contracts/python/aws_friendly_counsellor_contracts/__init__.py`
- `packages/contracts/python/aws_friendly_counsellor_contracts/models.py`
- `scripts/deploy_environment.sh`
- `scripts/generate_supply_chain_evidence.py`
- `scripts/validate_environment_config.py`
- `supply-chain/evidence.sha256`
- `supply-chain/sbom.cdx.json`
- `tests/conftest.py`
- `tests/test_api_v1.py`
- `tests/test_contracts.py`
- `tests/test_deploy_script.py`
- `tests/test_dynamodb_store.py`
- `tests/test_m14_authorization.py`
- `tests/test_m14_operations.py`
- `tests/test_persistence_api.py`
- `tests/test_repository_structure.py`
- `tests/test_security.py`

## Patch-file SHA-256

`5b8881870322cb804e283f8a14d13e4982dbbdf0c72c6a2b4f766525ef80f5ee`  `.env.example`
`2c2d738b53cb176267c9d3c4543391ad4c1b7b70d5e8ce7b8a053785e3cbfe16`  `.github/workflows/release-pipeline.yml`
`6ece6f1bc9c3edf9418ab8f74efbf3779b3673629c0dbe1c6416c365d131f1ea`  `CHANGELOG.md`
`2cc6c3d0865419f9b51a161c52563dea87130f3b29869977aac0271ddc8440d6`  `FILE_MANIFEST.sha256`
`dd4dfe7513419d63001a9b9abd019a1825efc0993e243c9a5ef2f8fed34d3004`  `Makefile`
`e48f38b9234a965f4b1497caa619a00c1980ac9f8abc86cd5eba22073dedd5ca`  `README.md`
`6ff946e1b1c1c46a6c3dad610a2edfab2a44fb049d0ea297f904c35e03f57cb0`  `apps/api/src/aws_friendly_counsellor/api/v1/common.py`
`2b827d5cc9dcb6bf3b666cab6b8a841269af9158ee5992136430a2e5c008deec`  `apps/api/src/aws_friendly_counsellor/api/v1/resources.py`
`1b1f3e6140df7719a89321e47bbfe4702d48be13d020ba582d1f940878e6ad4b`  `apps/api/src/aws_friendly_counsellor/core/config.py`
`7df174d0453febb69d6f698ed28cb13d3fd82688e79d76e315fa7c9033dfeba9`  `apps/api/src/aws_friendly_counsellor/domain/entities.py`
`42100a2cfaf3bde00620c31d9c07a3403d5edf558297a25991e67f75987d0a2c`  `apps/api/src/aws_friendly_counsellor/domain/repositories.py`
`cb3fdf37b795e583aba6d553c1b4610b5cd9983c863858caf6f3862916be268a`  `apps/api/src/aws_friendly_counsellor/infrastructure/persistence/dynamodb_store.py`
`fe4daab40e1c38670afc13d93b080121d7979d671c26e716efc63c91f6c5e2d2`  `apps/api/src/aws_friendly_counsellor/infrastructure/persistence/sqlite_store.py`
`404f0b1bb10832db5b2ad3cda168be616a704ec167160c0ee6dd1e4d047f17c1`  `apps/api/src/aws_friendly_counsellor/main.py`
`b7b2db9c99f4af541e588614f44c728167149dfb35863a70d8b0b602dcaae69f`  `apps/api/src/aws_friendly_counsellor/security/auth.py`
`00a25404704ee41dfa560c7086b6c20bf4529374ab599d97018fc16e014c74f8`  `apps/api/src/aws_friendly_counsellor/security/authorization.py`
`7c65dad7c375ccc28f8f83fc10c0de413ac0c0e731c90866f129866dc27973b7`  `docs/API_VERSIONING.md`
`fe249567e16207eb1a70da30728bec1338385f0bd454eafea117b1bcdf90d09e`  `docs/ARCHITECTURE.md`
`81f83e31f074b1f940ed5bd24c05bd728ebbd2011746a07dd456d6cc4e7c8bf0`  `docs/CI_CD.md`
`5aa4ebb0dec463ec64f2bca64db9681fd0acaa1a2e5e69a1bd68e1ba58e29507`  `docs/DATA_MODEL.md`
`4e91b70eeaceac2907020223c68dd1a3e3b3f8880c4167b8c5c40983e03e5ca2`  `docs/ENVIRONMENTS.md`
`0769501bb2cd6b9577a35c2dc74b259cc74f23fac89c4f42abee4f6f0666578a`  `docs/IDENTITY_AUTHORIZATION.md`
`0bfc8cb420e0e25dd1cacf5872ac53488c2f0085a701debf55b65869daa4e849`  `docs/ROLLBACK_RUNBOOK.md`
`896e4efc142faeb602fe055ac4a79ef6a59499081a78b3e82fd2971b98b92348`  `docs/SECURITY.md`
`8511a782eacefa6f4cd73fe58fcc553acb22c6cc9490ccf1a888dd3704f765f9`  `docs/THREAT_MODEL.md`
`9c12fdf8f55acb3df5567f27c080c1bec77d253fa1900992899dfc2661ac0a5b`  `docs/adr/0004-managed-identity-membership-audit.md`
`44191137597e850f12be0ef755336a78fea02fbe7706d5b855f489e7cdd53281`  `docs/reports/M1_4_VALIDATION_REPORT.md`
`35bc465ec5facfb62086b31f00de40a7d64deb5de5c963f83a884c59d6aaf58a`  `infra/bootstrap/github-oidc.yaml`
`9289eb33a7cbde76da877504da12a3739ea9bc70c4222d76834ab37f02b73f58`  `infra/sam/environments/dev.env`
`45e402a7144a9da1b0df2c2904ed50b1bb28b0e284d88939c88b9140c26b34c0`  `infra/sam/environments/production.env`
`152466d9fdcc1d9573067db7ac43e46438c9640cee87a2a028f7490dd4a0fc2b`  `infra/sam/environments/staging.env`
`cdb126150c1457d519509be34f0c4c18db15b8a5e155a43da87afad458fe44d5`  `infra/sam/samconfig.toml`
`7cd1297d1fb6a1570dcb1f137111fbcb3025e9e2511a8bd02a061547a41cc8ef`  `infra/sam/template.yaml`
`8146a83304ec92183f64d3542b1dc3be1dca89671be241de3fd904686932e1ba`  `packages/contracts/CHANGELOG.md`
`baa7a0cba964d32b788e7fe2cc80cd38b889d58ff74fac47c0875bb52f354f60`  `packages/contracts/README.md`
`5aa5cb7a3595a86bc1cff8e6444f7ca9a07136731f7ee454f9747a05681104dd`  `packages/contracts/jsonschema/v1/AuditEventListResponse.schema.json`
`acfd43ad4f9c468a7937a94ad39de796be43abcd855cdbbeb4b6f4632458c54e`  `packages/contracts/jsonschema/v1/IdentityResponse.schema.json`
`9186eecda9ff8020f63465777fae6940f87ab73eaddece750a4e17ce4cfcc0cf`  `packages/contracts/jsonschema/v1/TenantMembershipCreateRequest.schema.json`
`33d9ea090da6581358cd754dc03ca0095d9de3ed9e5b39b1e5b22aba041813d4`  `packages/contracts/jsonschema/v1/TenantMembershipListResponse.schema.json`
`369a7e1ff1a55a8afd89f17ec0dc8145f8d7cb42559f37097c65593113b67ece`  `packages/contracts/jsonschema/v1/TenantMembershipResponse.schema.json`
`53d55407024e53c379c9cc5e246cba4b957cbf065d040f5a3174d890e8040351`  `packages/contracts/jsonschema/v1/TenantMembershipUpdateRequest.schema.json`
`f2fa6e6db59e079b55119e1eb880840c665f92dee9e37fb53b502004a9ba0b52`  `packages/contracts/openapi/v1/openapi.json`
`b574fc8f1f9efe7c9d2e4a9a20b2c52789b0f281cc433e91ce1ff5911c113ad7`  `packages/contracts/python/aws_friendly_counsellor_contracts/__init__.py`
`accf9d22c4e815b2e1f4e8f9cd7415f471d4507244a7cf4763fd0f959c5bb0af`  `packages/contracts/python/aws_friendly_counsellor_contracts/models.py`
`7d43cda069082d99b061f7118d375ffb5073b1cd706f8357ac06569c1efd0baa`  `scripts/deploy_environment.sh`
`450a88934aa99bc3a3aa08d762aced6b6163e6b094d4b2522c5288de70708150`  `scripts/generate_supply_chain_evidence.py`
`c8c3646344906aefb5b2b9e307bcf1b4aebad51038ca0363b95328cf531f5187`  `scripts/validate_environment_config.py`
`9670b79d59e3a9728d05e17624563d81eb4c5e79017a2fcd24f0c19ba59cfc08`  `supply-chain/evidence.sha256`
`4f7d93fee2ed0fa6eafe937536450b2202c2d597fbf7133b197ad86b61d0162f`  `supply-chain/sbom.cdx.json`
`476c620eb84a10647dbdba366db50b5ac90cf9696111464c8d9e0e7f1b7304a1`  `tests/conftest.py`
`af3af2f27908e624ead0ede0094f6fff5b8fd2aa4d214bbc5d7575c624e1a8b3`  `tests/test_api_v1.py`
`53a92499f98bd0af2bded10d2e766a63dbac46d286df6db172f51c0956f96114`  `tests/test_contracts.py`
`1837a50312912f0bf3c7e62b4aabbf246f4cd55729302e4bdbb014bfbc493b89`  `tests/test_deploy_script.py`
`5912f2987d78699f1de9ee59415b383e8a1858479193e35688584b4f9f81f017`  `tests/test_dynamodb_store.py`
`81a1d46514ea871ea3d1f9079a266734011e8136ac43bd68ca39b6680dc44205`  `tests/test_m14_authorization.py`
`5267868097672ad0557afc06d8191372e37d9872a4ec54fd037fb2ccebeda462`  `tests/test_m14_operations.py`
`28828aa86c1be94ba22cfc3210431313220e8e9d12c8ac76fcf206ff40761cf5`  `tests/test_persistence_api.py`
`3deb20dd358fc75d2ecdbe1d1bdc83c85e0452690de322221d3fcdff89c5443e`  `tests/test_repository_structure.py`
`8640b170b0fb7ed6a45d382e0fa3cf832807b6b0f27fb964b5b922b0b57d3b43`  `tests/test_security.py`

## Validation boundary

Local structural/application validation is complete. Real SAM/Docker/AWS deployment, Cognito sign-in, live API Gateway authorization, live DynamoDB integration, and canary rollback were not executed in the local execution environment and are not claimed as proven.
