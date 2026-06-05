#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

AWS_REGION="${AWS_REGION:-ap-southeast-2}"
SECRET_ID="${GCP_SECRET_ID:-gcp-firestore-service-account}"
TMP_JSON="$(mktemp)"

cleanup() {
  rm -f "$TMP_JSON"
}
trap cleanup EXIT

cd "$ROOT/gcp/infra"
terraform output -raw aws_dispatcher_key_json_base64 | base64 --decode > "$TMP_JSON"

if aws secretsmanager describe-secret --secret-id "$SECRET_ID" --region "$AWS_REGION" >/dev/null 2>&1; then
  aws secretsmanager put-secret-value \
    --secret-id "$SECRET_ID" \
    --secret-string "file://$TMP_JSON" \
    --region "$AWS_REGION" >/dev/null
  echo "Updated AWS Secrets Manager secret: $SECRET_ID"
else
  aws secretsmanager create-secret \
    --name "$SECRET_ID" \
    --secret-string "file://$TMP_JSON" \
    --region "$AWS_REGION" >/dev/null
  echo "Created AWS Secrets Manager secret: $SECRET_ID"
fi

