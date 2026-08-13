.PHONY: install test coverage compile contracts contracts-check db-init env-check supply-chain supply-chain-check manifest package validate clean build-AnalyzeFunction

install:
	python -m pip install -r requirements-dev.txt

test:
	pytest -q

coverage:
	pytest --cov --cov-report=term-missing -q

compile:
	python -m compileall -q apps packages scripts tests

contracts:
	python scripts/export_contracts.py

contracts-check:
	python scripts/export_contracts.py --check

db-init:
	python scripts/migrate_local_database.py

env-check:
	python scripts/validate_environment_config.py

supply-chain:
	python scripts/generate_supply_chain_evidence.py

supply-chain-check:
	python scripts/generate_supply_chain_evidence.py --check

manifest:
	python scripts/generate_manifest.py

package:
	./scripts/package_lambda.sh

validate: compile contracts-check env-check supply-chain-check coverage

# AWS SAM custom builder. SAM executes this target inside the architecture-matched
# build container; ARTIFACTS_DIR is supplied by SAM.
build-AnalyzeFunction:
	python -m pip install --no-compile --target "$(ARTIFACTS_DIR)" -r apps/api/requirements.txt
	cp -R apps/api/src/aws_friendly_counsellor "$(ARTIFACTS_DIR)/"
	cp -R packages/contracts/python/aws_friendly_counsellor_contracts "$(ARTIFACTS_DIR)/"
	find "$(ARTIFACTS_DIR)" -type d -name __pycache__ -prune -exec rm -rf {} +
	find "$(ARTIFACTS_DIR)" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

clean:
	rm -rf .pytest_cache .coverage htmlcov dist build .local
	find . -type d -name .aws-sam -prune -exec rm -rf {} +
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
