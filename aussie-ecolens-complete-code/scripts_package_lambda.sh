#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: ./scripts_package_lambda.sh <lambda_folder>"
  echo "Example: ./scripts_package_lambda.sh presign_upload"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")" && pwd)"
NAME="$1"
SRC="$ROOT/aws/lambdas/$NAME"
OUT="$ROOT/build/$NAME"

if [ ! -f "$SRC/handler.py" ]; then
  echo "No handler found at $SRC/handler.py"
  exit 1
fi

rm -rf "$OUT"
mkdir -p "$OUT"
rm -f "$ROOT/build/$NAME.zip"
cp -R "$ROOT/aws/lambdas/common" "$OUT/common"
cp "$SRC/handler.py" "$OUT/handler.py"
python3 -m pip install \
  --quiet \
  --disable-pip-version-check \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.12 \
  --only-binary=:all: \
  -r "$ROOT/aws/lambdas/requirements.txt" \
  -t "$OUT"

(
  cd "$OUT"
  zip -qr "../$NAME.zip" .
)

echo "Created build/$NAME.zip"
