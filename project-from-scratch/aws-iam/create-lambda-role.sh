#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-ap-southeast-2}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:?Set AWS_ACCOUNT_ID}"
LAMBDA_ROLE_NAME="${LAMBDA_ROLE_NAME:-ecolens-lambda-execution-role}"
UPLOAD_BUCKET="${UPLOAD_BUCKET:-ecolens-upload-bucket}"
MEDIA_TABLE="${MEDIA_TABLE:-ecolens-media}"
CHECKSUM_TABLE="${CHECKSUM_TABLE:-ecolens-checksums}"
SUBSCRIPTIONS_TABLE="${SUBSCRIPTIONS_TABLE:-ecolens-subscriptions}"
SETTINGS_TABLE="${SETTINGS_TABLE:-ecolens-settings}"
SNS_TOPIC_PREFIX="${SNS_TOPIC_PREFIX:-ecolens-}"
GCP_WIF_SECRET_NAME="${GCP_WIF_SECRET_NAME:-ecolens-gcp-wif-credential-config}"

ROLE_ARN="$(
  aws iam get-role --role-name "${LAMBDA_ROLE_NAME}" --query 'Role.Arn' --output text 2>/dev/null || true
)"

if [[ -z "${ROLE_ARN}" ]]; then
  ROLE_ARN="$(
    aws iam create-role \
      --role-name "${LAMBDA_ROLE_NAME}" \
      --assume-role-policy-document file://lambda-trust-policy.json \
      --query 'Role.Arn' \
      --output text
  )"
fi

POLICY_DOC="$(mktemp)"
sed \
  -e "s/ecolens-upload-bucket/${UPLOAD_BUCKET}/g" \
  -e "s/ecolens-media/${MEDIA_TABLE}/g" \
  -e "s/ecolens-checksums/${CHECKSUM_TABLE}/g" \
  -e "s/ecolens-subscriptions/${SUBSCRIPTIONS_TABLE}/g" \
  -e "s/ecolens-settings/${SETTINGS_TABLE}/g" \
  -e "s/397450412956/${AWS_ACCOUNT_ID}/g" \
  -e "s/ap-southeast-2/${AWS_REGION}/g" \
  -e "s/ecolens-\\*/${SNS_TOPIC_PREFIX}*/g" \
  -e "s/ecolens-gcp-wif-credential-config/${GCP_WIF_SECRET_NAME}/g" \
  lambda-execution-policy.json > "${POLICY_DOC}"

aws iam put-role-policy \
  --role-name "${LAMBDA_ROLE_NAME}" \
  --policy-name EcolensLambdaExecutionPolicy \
  --policy-document "file://${POLICY_DOC}"

echo "LAMBDA_ROLE_ARN=${ROLE_ARN}"

