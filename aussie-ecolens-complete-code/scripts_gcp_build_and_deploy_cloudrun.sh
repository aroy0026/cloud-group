#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID.}"
: "${GCP_PROCESSING_BUCKET:?Set GCP_PROCESSING_BUCKET.}"

GCP_REGION="${GCP_REGION:-australia-southeast1}"
ARTIFACT_REPOSITORY="${ARTIFACT_REPOSITORY:-aussie-ecolens}"
IMAGE="$GCP_REGION-docker.pkg.dev/$GCP_PROJECT_ID/$ARTIFACT_REPOSITORY/processor:latest"

"$ROOT/scripts_prepare_models.sh"

gcloud auth configure-docker "$GCP_REGION-docker.pkg.dev"
gcloud builds submit "$ROOT/gcp/cloudrun_processor" --tag "$IMAGE" --project "$GCP_PROJECT_ID"

cd "$ROOT/gcp/infra"
terraform apply \
  -var "project_id=$GCP_PROJECT_ID" \
  -var "region=$GCP_REGION" \
  -var "processing_bucket=$GCP_PROCESSING_BUCKET" \
  -var "cloud_run_image=$IMAGE"

echo "Cloud Run deployed."
terraform output cloud_run_url
echo "Use this URL with /query-file when setting AWS query_file_processor_url."

