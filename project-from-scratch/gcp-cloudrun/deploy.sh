#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-project-b70b0656-b022-41bd-bc6}"
REGION="${REGION:-australia-southeast1}"
SERVICE="${SERVICE:-aussie-ecolens-processor}"
REPOSITORY="${REPOSITORY:-aussie-ecolens}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/processor:latest"
GCS_BUCKET="${GCS_BUCKET:-aussie-ecolens-processing-project-b70b0656-b022-41bd-bc6}"
CONFIDENCE_THRESHOLD="${CONFIDENCE_THRESHOLD:-0.20}"

if [[ ! -f model.pt || ! -f mdv5a.pt ]]; then
  echo "Missing model.pt or mdv5a.pt. See MODEL_FILES.md." >&2
  exit 1
fi

gcloud config set project "${PROJECT_ID}"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
gcloud builds submit . --tag "${IMAGE}" --project "${PROJECT_ID}"
gcloud run deploy "${SERVICE}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --memory 4Gi \
  --cpu 2 \
  --timeout 900 \
  --concurrency 1 \
  --no-allow-unauthenticated \
  --set-env-vars "GCS_BUCKET=${GCS_BUCKET},CONFIDENCE_THRESHOLD=${CONFIDENCE_THRESHOLD}"

