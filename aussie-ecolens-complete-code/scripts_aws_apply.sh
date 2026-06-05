#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

: "${AWS_UPLOAD_BUCKET:?Set AWS_UPLOAD_BUCKET.}"
: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID.}"
: "${GCP_PROCESSING_BUCKET:?Set GCP_PROCESSING_BUCKET.}"

AWS_REGION="${AWS_REGION:-ap-southeast-2}"
PROJECT_NAME="${PROJECT_NAME:-aussie-ecolens}"
FRONTEND_ORIGIN="${FRONTEND_ORIGIN:-http://localhost:5173}"
COGNITO_USER_POOL_ID="${COGNITO_USER_POOL_ID:-ap-southeast-2_y1ddoO0pv}"
COGNITO_CLIENT_ID="${COGNITO_CLIENT_ID:-22jl47515ubj2b3ib3j8qm2o6i}"
GCP_REGION="${GCP_REGION:-australia-southeast1}"
GCP_SECRET_ID="${GCP_SECRET_ID:-gcp-firestore-service-account}"
PUBSUB_TOPIC="${PUBSUB_TOPIC:-projects/$GCP_PROJECT_ID/topics/media-processing}"
QUERY_FILE_PROCESSOR_URL="${QUERY_FILE_PROCESSOR_URL:-}"

"$ROOT/scripts_package_all_lambdas.sh"

cd "$ROOT/aws/infra"
terraform init
terraform apply \
  -var "aws_region=$AWS_REGION" \
  -var "project_name=$PROJECT_NAME" \
  -var "upload_bucket=$AWS_UPLOAD_BUCKET" \
  -var "frontend_origin=$FRONTEND_ORIGIN" \
  -var "cognito_user_pool_id=$COGNITO_USER_POOL_ID" \
  -var "cognito_client_id=$COGNITO_CLIENT_ID" \
  -var "gcp_secret_id=$GCP_SECRET_ID" \
  -var "gcp_bucket=$GCP_PROCESSING_BUCKET" \
  -var "gcp_project_id=$GCP_PROJECT_ID" \
  -var "pubsub_topic=$PUBSUB_TOPIC" \
  -var "query_file_processor_url=$QUERY_FILE_PROCESSOR_URL"

API_URL="$(terraform output -raw api_endpoint)"
VITE_API_BASE_URL="$API_URL" \
VITE_AWS_REGION="$AWS_REGION" \
VITE_COGNITO_USER_POOL_ID="$COGNITO_USER_POOL_ID" \
VITE_COGNITO_CLIENT_ID="$COGNITO_CLIENT_ID" \
  "$ROOT/scripts_write_frontend_env.sh"

echo "AWS apply complete."
echo "API endpoint: $API_URL"
