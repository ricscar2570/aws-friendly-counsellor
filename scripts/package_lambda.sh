#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build/lambda"
DIST_DIR="$ROOT_DIR/dist"
TARGET_ARCH="${TARGET_ARCH:-arm64}"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"

case "$TARGET_ARCH" in
  arm64) PLATFORM="manylinux2014_aarch64" ;;
  x86_64) PLATFORM="manylinux2014_x86_64" ;;
  *) echo "TARGET_ARCH must be arm64 or x86_64" >&2; exit 2 ;;
esac

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"
if [[ "${SKIP_DEPENDENCIES:-false}" != "true" ]]; then
  python -m pip install \
    --upgrade \
    --no-compile \
    --only-binary=:all: \
    --implementation cp \
    --python-version "$PYTHON_VERSION" \
    --platform "$PLATFORM" \
    --target "$BUILD_DIR" \
    -r "$ROOT_DIR/apps/api/requirements.txt"
else
  echo "Skipping dependency installation for source-layout verification"
fi
cp -R "$ROOT_DIR/apps/api/src/aws_friendly_counsellor" "$BUILD_DIR/"
cp -R "$ROOT_DIR/packages/contracts/python/aws_friendly_counsellor_contracts" "$BUILD_DIR/"
find "$BUILD_DIR" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$BUILD_DIR" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
(
  cd "$BUILD_DIR"
  zip -qr "$DIST_DIR/aws-friendly-counsellor-lambda-${TARGET_ARCH}.zip" .
)
echo "Created $DIST_DIR/aws-friendly-counsellor-lambda-${TARGET_ARCH}.zip"
