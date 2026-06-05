#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

for name in presign_upload ingest_dispatcher query_api tag_api delete_api notification_api; do
  "$ROOT/scripts_package_lambda.sh" "$name"
done

echo "All Lambda packages are ready in $ROOT/build."

