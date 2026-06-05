#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-ap-southeast-2}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:?Set AWS_ACCOUNT_ID}"
UPLOAD_BUCKET="${UPLOAD_BUCKET:?Set UPLOAD_BUCKET}"
LAMBDA_ROLE_ARN="${LAMBDA_ROLE_ARN:?Set LAMBDA_ROLE_ARN}"
LAMBDA_ARTIFACT_PREFIX="${LAMBDA_ARTIFACT_PREFIX:-lambda-artifacts}"

MEDIA_TABLE="${MEDIA_TABLE:-ecolens-media}"
CHECKSUM_TABLE="${CHECKSUM_TABLE:-ecolens-checksums}"
SUBSCRIPTIONS_TABLE="${SUBSCRIPTIONS_TABLE:-ecolens-subscriptions}"
SETTINGS_TABLE="${SETTINGS_TABLE:-ecolens-settings}"
CORS_ORIGIN="${CORS_ORIGIN:-http://localhost:5173}"
SNS_TOPIC_PREFIX="${SNS_TOPIC_PREFIX:-ecolens-}"
SIGNED_URL_EXPIRES="${SIGNED_URL_EXPIRES:-900}"
GET_URL_EXPIRES="${GET_URL_EXPIRES:-3600}"
QUERY_FILE_PROCESSOR_URL="${QUERY_FILE_PROCESSOR_URL:-${CLOUD_RUN_URL:-}/query-file}"
CLOUD_RUN_AUDIENCE="${CLOUD_RUN_AUDIENCE:-${CLOUD_RUN_URL:-}}"
QUERY_FILE_PROCESSOR_TIMEOUT="${QUERY_FILE_PROCESSOR_TIMEOUT:-120}"
GCP_WIF_CREDENTIAL_CONFIG_SECRET="${GCP_WIF_CREDENTIAL_CONFIG_SECRET:-ecolens-gcp-wif-credential-config}"
GCP_SERVICE_ACCOUNT_EMAIL="${GCP_SERVICE_ACCOUNT_EMAIL:?Set GCP_SERVICE_ACCOUNT_EMAIL}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST="${ROOT}/dist"

if [[ ! -d "${DIST}" ]]; then
  echo "Missing ${DIST}. Run ./package-lambdas.sh first." >&2
  exit 1
fi

common_env="SIGNED_URL_EXPIRES=${SIGNED_URL_EXPIRES},GET_URL_EXPIRES=${GET_URL_EXPIRES},SUBSCRIPTIONS_TABLE=${SUBSCRIPTIONS_TABLE},CHECKSUM_TABLE=${CHECKSUM_TABLE},UPLOAD_BUCKET=${UPLOAD_BUCKET},MEDIA_TABLE=${MEDIA_TABLE},CORS_ORIGIN=${CORS_ORIGIN},SETTINGS_TABLE=${SETTINGS_TABLE},SNS_TOPIC_PREFIX=${SNS_TOPIC_PREFIX}"
wif_env="${common_env},QUERY_FILE_PROCESSOR_URL=${QUERY_FILE_PROCESSOR_URL},QUERY_FILE_PROCESSOR_TIMEOUT=${QUERY_FILE_PROCESSOR_TIMEOUT},CLOUD_RUN_AUDIENCE=${CLOUD_RUN_AUDIENCE},GCP_WIF_CREDENTIAL_CONFIG_SECRET=${GCP_WIF_CREDENTIAL_CONFIG_SECRET},GCP_SERVICE_ACCOUNT_EMAIL=${GCP_SERVICE_ACCOUNT_EMAIL}"
media_env="${wif_env},THUMBNAIL_MAX_DIMENSION=480,THUMBNAIL_QUALITY=78,VIDEO_MAX_FRAMES=12,VIDEO_FRAME_JPEG_QUALITY=82"

deploy_one() {
  local folder="$1"
  local function_name="$2"
  local timeout="$3"
  local memory="$4"
  local env_vars="$5"
  local key="${LAMBDA_ARTIFACT_PREFIX}/${folder}.zip"

  aws s3 cp "${DIST}/${folder}.zip" "s3://${UPLOAD_BUCKET}/${key}" --region "${AWS_REGION}" >/dev/null

  if aws lambda get-function --function-name "${function_name}" --region "${AWS_REGION}" >/dev/null 2>&1; then
    aws lambda update-function-code \
      --function-name "${function_name}" \
      --s3-bucket "${UPLOAD_BUCKET}" \
      --s3-key "${key}" \
      --region "${AWS_REGION}" >/dev/null
    aws lambda wait function-updated --function-name "${function_name}" --region "${AWS_REGION}"
  else
    aws lambda create-function \
      --function-name "${function_name}" \
      --runtime python3.12 \
      --handler handler.handler \
      --role "${LAMBDA_ROLE_ARN}" \
      --code "S3Bucket=${UPLOAD_BUCKET},S3Key=${key}" \
      --timeout "${timeout}" \
      --memory-size "${memory}" \
      --environment "Variables={${env_vars}}" \
      --region "${AWS_REGION}" >/dev/null
    aws lambda wait function-active --function-name "${function_name}" --region "${AWS_REGION}"
  fi

  aws lambda update-function-configuration \
    --function-name "${function_name}" \
    --timeout "${timeout}" \
    --memory-size "${memory}" \
    --environment "Variables={${env_vars}}" \
    --region "${AWS_REGION}" >/dev/null
  echo "deployed: ${function_name}"
}

deploy_one files_delete ecolens-files-delete 30 128 "${common_env}"
deploy_one files_list ecolens-files-list 30 128 "${common_env}"
deploy_one notifications_settings ecolens-notifications-settings 30 128 "${common_env}"
deploy_one notifications_subscriptions ecolens-notifications-subscriptions 30 128 "${common_env}"
deploy_one query_by_file ecolens-query-by-file 120 512 "${wif_env}"
deploy_one query_by_species ecolens-query-by-species 30 128 "${common_env}"
deploy_one query_by_tags ecolens-query-by-tags 30 128 "${common_env}"
deploy_one query_by_thumbnail ecolens-query-by-thumbnail 30 128 "${common_env}"
deploy_one tags_bulk_edit ecolens-tags-bulk-edit 30 128 "${common_env}"
deploy_one upload ecolens-upload 30 128 "${common_env}"
deploy_one upload_complete ecolens-upload-complete 60 512 "${common_env}"
deploy_one upload_prepare ecolens-upload-prepare 30 128 "${common_env}"
deploy_one media_processor ecolens-media-processor 180 1024 "${media_env}"

