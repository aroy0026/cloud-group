#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-ap-southeast-2}"
UPLOAD_BUCKET="${UPLOAD_BUCKET:?Set UPLOAD_BUCKET}"
CORS_ORIGIN="${CORS_ORIGIN:-http://localhost:5173}"

if ! aws s3api head-bucket --bucket "${UPLOAD_BUCKET}" 2>/dev/null; then
  aws s3api create-bucket \
    --bucket "${UPLOAD_BUCKET}" \
    --region "${AWS_REGION}" \
    --create-bucket-configuration "LocationConstraint=${AWS_REGION}"
fi

aws s3api put-public-access-block \
  --bucket "${UPLOAD_BUCKET}" \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

CORS_FILE="$(mktemp)"
python3 - "$CORS_ORIGIN" > "${CORS_FILE}" <<'PY'
import json
import sys

origin = sys.argv[1]
print(json.dumps({
    "CORSRules": [
        {
            "AllowedOrigins": [origin],
            "AllowedMethods": ["GET", "PUT", "POST", "HEAD"],
            "AllowedHeaders": ["*"],
            "ExposeHeaders": ["ETag"],
            "MaxAgeSeconds": 3000,
        }
    ]
}))
PY

aws s3api put-bucket-cors \
  --bucket "${UPLOAD_BUCKET}" \
  --cors-configuration "file://${CORS_FILE}"

echo "ready: s3://${UPLOAD_BUCKET}"

