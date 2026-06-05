#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-ap-southeast-2}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:?Set AWS_ACCOUNT_ID}"
UPLOAD_BUCKET="${UPLOAD_BUCKET:?Set UPLOAD_BUCKET}"
FUNCTION_NAME="${FUNCTION_NAME:-ecolens-media-processor}"

FUNCTION_ARN="$(
  aws lambda get-function \
    --function-name "${FUNCTION_NAME}" \
    --region "${AWS_REGION}" \
    --query 'Configuration.FunctionArn' \
    --output text
)"

aws lambda add-permission \
  --function-name "${FUNCTION_NAME}" \
  --statement-id "AllowS3Invoke-${UPLOAD_BUCKET}" \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn "arn:aws:s3:::${UPLOAD_BUCKET}" \
  --source-account "${AWS_ACCOUNT_ID}" \
  --region "${AWS_REGION}" >/dev/null 2>&1 || true

CONFIG="$(mktemp)"
python3 - "$FUNCTION_ARN" > "${CONFIG}" <<'PY'
import json
import sys

function_arn = sys.argv[1]
print(json.dumps({
    "LambdaFunctionConfigurations": [
        {
            "Id": "ecolens-media-processor-uploads",
            "LambdaFunctionArn": function_arn,
            "Events": ["s3:ObjectCreated:*"],
            "Filter": {
                "Key": {
                    "FilterRules": [
                        {"Name": "prefix", "Value": "uploads/"}
                    ]
                }
            }
        }
    ]
}))
PY

aws s3api put-bucket-notification-configuration \
  --bucket "${UPLOAD_BUCKET}" \
  --notification-configuration "file://${CONFIG}" \
  --region "${AWS_REGION}"

echo "configured S3 trigger for ${UPLOAD_BUCKET} -> ${FUNCTION_NAME}"

