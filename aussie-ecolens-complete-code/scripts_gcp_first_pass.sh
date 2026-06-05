#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID.}"
: "${GCP_PROCESSING_BUCKET:?Set GCP_PROCESSING_BUCKET.}"

GCP_REGION="${GCP_REGION:-australia-southeast1}"

cd "$ROOT/gcp/infra"
terraform init
terraform apply \
  -var "project_id=$GCP_PROJECT_ID" \
  -var "region=$GCP_REGION" \
  -var "processing_bucket=$GCP_PROCESSING_BUCKET" \
  -var "cloud_run_image="

echo "GCP first pass complete. Artifact Registry, bucket, Pub/Sub, and service accounts are ready."
echo "Next: run scripts_gcp_build_and_deploy_cloudrun.sh"

