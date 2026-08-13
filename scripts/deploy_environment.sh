#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-}"

case "$TARGET" in
  dev|staging|production) ;;
  *) echo "Usage: $0 {dev|staging|production}" >&2; exit 2 ;;
esac

: "${RELEASE_VERSION:?RELEASE_VERSION is required}"
GIT_SHA="${GIT_SHA:-$(git -C "$ROOT_DIR" rev-parse HEAD)}"
: "${ALLOWED_ORIGINS:?ALLOWED_ORIGINS is required}"
: "${SAM_ARTIFACT_BUCKET:?SAM_ARTIFACT_BUCKET is required}"
: "${CLOUDFORMATION_EXECUTION_ROLE_ARN:?CLOUDFORMATION_EXECUTION_ROLE_ARN is required}"

ENABLE_GRADUAL_DEPLOYMENT="${ENABLE_GRADUAL_DEPLOYMENT:-false}"
RATE_LIMIT_REQUESTS="${RATE_LIMIT_REQUESTS:-100}"
RATE_LIMIT_WINDOW="${RATE_LIMIT_WINDOW:-3600}"
DATA_TABLE_NAME="${DATA_TABLE_NAME:-}"

if [[ "$ENABLE_GRADUAL_DEPLOYMENT" != "true" && "$ENABLE_GRADUAL_DEPLOYMENT" != "false" ]]; then
  echo "ENABLE_GRADUAL_DEPLOYMENT must be true or false" >&2
  exit 2
fi
if [[ ! "$GIT_SHA" =~ ^([0-9a-fA-F]{7,64}|unknown)$ ]]; then
  echo "GIT_SHA is not a valid commit identifier" >&2
  exit 2
fi

python "$ROOT_DIR/scripts/validate_release_ref.py" --environment "$TARGET" --ref "$RELEASE_VERSION" >/dev/null
if ACTUAL_GIT_SHA=$(git -C "$ROOT_DIR" rev-parse HEAD 2>/dev/null); then
  if [[ "$GIT_SHA" != "unknown" && "$GIT_SHA" != "$ACTUAL_GIT_SHA" ]]; then
    echo "GIT_SHA does not match the checked-out source" >&2
    exit 2
  fi
fi

PROFILE_FILE="$ROOT_DIR/infra/sam/environments/$TARGET.env"
if [[ ! -f "$PROFILE_FILE" ]]; then
  echo "Missing environment profile: $PROFILE_FILE" >&2
  exit 2
fi

# The profile files are trusted repository configuration and contain only KEY=value pairs.
while IFS='=' read -r key value; do
  [[ -z "$key" || "$key" == \#* ]] && continue
  if [[ ! "$key" =~ ^[A-Z0-9_]+$ || "$value" =~ [[:space:]] ]]; then
    echo "Invalid environment profile line for $key" >&2
    exit 2
  fi
  printf -v "$key" '%s' "$value"
done < "$PROFILE_FILE"

if [[ "${FORCE_ALL_AT_ONCE:-false}" == "true" ]]; then
  ENABLE_GRADUAL_DEPLOYMENT=false
  DEPLOYMENT_PREFERENCE_TYPE=AllAtOnce
fi

PARAMETERS=(
  "EnvironmentName=$TARGET"
  "ReleaseVersion=$RELEASE_VERSION"
  "GitSha=$GIT_SHA"
  "AllowSelfRegistration=$ALLOW_SELF_REGISTRATION"
  "AllowedOrigins=$ALLOWED_ORIGINS"
  "RateLimitRequests=$RATE_LIMIT_REQUESTS"
  "RateLimitWindow=$RATE_LIMIT_WINDOW"
  "LogLevel=$LOG_LEVEL"
  "LogRetentionDays=$LOG_RETENTION_DAYS"
  "ReservedConcurrentExecutions=$RESERVED_CONCURRENT_EXECUTIONS"
  "EnableGradualDeployment=$ENABLE_GRADUAL_DEPLOYMENT"
  "DeploymentPreferenceType=$DEPLOYMENT_PREFERENCE_TYPE"
  "EnableContributorInsights=$ENABLE_CONTRIBUTOR_INSIGHTS"
  "EnableTableDeletionProtection=$ENABLE_TABLE_DELETION_PROTECTION"
)
if [[ -n "$DATA_TABLE_NAME" ]]; then
  PARAMETERS+=("DataTableName=$DATA_TABLE_NAME")
fi

cd "$ROOT_DIR/infra/sam"
if [[ "${SKIP_BUILD:-false}" != "true" ]]; then
  sam build --config-env "$TARGET" --use-container
elif [[ ! -f ".aws-sam/build/template.yaml" ]]; then
  echo "SKIP_BUILD=true but .aws-sam/build/template.yaml is missing" >&2
  exit 2
fi
sam deploy \
  --config-env "$TARGET" \
  --s3-bucket "$SAM_ARTIFACT_BUCKET" \
  --role-arn "$CLOUDFORMATION_EXECUTION_ROLE_ARN" \
  --on-failure ROLLBACK \
  --parameter-overrides "${PARAMETERS[@]}"
