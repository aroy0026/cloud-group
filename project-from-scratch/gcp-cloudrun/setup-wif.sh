#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-ap-southeast-2}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:?Set AWS_ACCOUNT_ID}"
LAMBDA_ROLE_NAME="${LAMBDA_ROLE_NAME:-ecolens-lambda-execution-role}"
GCP_PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
GCP_PROJECT_NUMBER="${GCP_PROJECT_NUMBER:?Set GCP_PROJECT_NUMBER}"
GCP_REGION="${GCP_REGION:-australia-southeast1}"
GCP_CLOUD_RUN_SERVICE="${GCP_CLOUD_RUN_SERVICE:-aussie-ecolens-processor}"
GCP_SERVICE_ACCOUNT_EMAIL="${GCP_SERVICE_ACCOUNT_EMAIL:?Set GCP_SERVICE_ACCOUNT_EMAIL}"
GCP_WIF_POOL_ID="${GCP_WIF_POOL_ID:-aws-lambda-pool}"
GCP_WIF_PROVIDER_ID="${GCP_WIF_PROVIDER_ID:-aws-provider}"
GCP_WIF_SECRET_NAME="${GCP_WIF_SECRET_NAME:-ecolens-gcp-wif-credential-config}"

gcloud services enable \
  iam.googleapis.com \
  sts.googleapis.com \
  iamcredentials.googleapis.com \
  run.googleapis.com \
  --project "${GCP_PROJECT_ID}"

if ! gcloud iam service-accounts describe "${GCP_SERVICE_ACCOUNT_EMAIL}" --project "${GCP_PROJECT_ID}" >/dev/null 2>&1; then
  SA_NAME="${GCP_SERVICE_ACCOUNT_EMAIL%@*}"
  gcloud iam service-accounts create "${SA_NAME}" \
    --project "${GCP_PROJECT_ID}" \
    --display-name "AWS EcoLens Cloud Run invoker"
fi

if ! gcloud iam workload-identity-pools describe "${GCP_WIF_POOL_ID}" --location=global --project "${GCP_PROJECT_ID}" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools create "${GCP_WIF_POOL_ID}" \
    --location=global \
    --project "${GCP_PROJECT_ID}" \
    --display-name "AWS Lambda federation"
fi

if ! gcloud iam workload-identity-pools providers describe "${GCP_WIF_PROVIDER_ID}" --location=global --workload-identity-pool="${GCP_WIF_POOL_ID}" --project "${GCP_PROJECT_ID}" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools providers create-aws "${GCP_WIF_PROVIDER_ID}" \
    --location=global \
    --workload-identity-pool="${GCP_WIF_POOL_ID}" \
    --project "${GCP_PROJECT_ID}" \
    --account-id="${AWS_ACCOUNT_ID}" \
    --display-name "AWS Lambda provider" \
    --attribute-mapping="google.subject=assertion.arn,attribute.aws_role=assertion.arn.extract('assumed-role/{role}/')" \
    --attribute-condition="assertion.arn.startsWith('arn:aws:sts::${AWS_ACCOUNT_ID}:assumed-role/${LAMBDA_ROLE_NAME}/')"
fi

MEMBER="principalSet://iam.googleapis.com/projects/${GCP_PROJECT_NUMBER}/locations/global/workloadIdentityPools/${GCP_WIF_POOL_ID}/attribute.aws_role/${LAMBDA_ROLE_NAME}"

gcloud iam service-accounts add-iam-policy-binding "${GCP_SERVICE_ACCOUNT_EMAIL}" \
  --project "${GCP_PROJECT_ID}" \
  --member "${MEMBER}" \
  --role roles/iam.workloadIdentityUser

gcloud iam service-accounts add-iam-policy-binding "${GCP_SERVICE_ACCOUNT_EMAIL}" \
  --project "${GCP_PROJECT_ID}" \
  --member "${MEMBER}" \
  --role roles/iam.serviceAccountOpenIdTokenCreator

gcloud run services add-iam-policy-binding "${GCP_CLOUD_RUN_SERVICE}" \
  --region "${GCP_REGION}" \
  --project "${GCP_PROJECT_ID}" \
  --member "serviceAccount:${GCP_SERVICE_ACCOUNT_EMAIL}" \
  --role roles/run.invoker

CRED_CONFIG="$(mktemp)"
gcloud iam workload-identity-pools create-cred-config \
  "projects/${GCP_PROJECT_NUMBER}/locations/global/workloadIdentityPools/${GCP_WIF_POOL_ID}/providers/${GCP_WIF_PROVIDER_ID}" \
  --aws \
  --output-file="${CRED_CONFIG}" \
  --project "${GCP_PROJECT_ID}"

if aws secretsmanager describe-secret --secret-id "${GCP_WIF_SECRET_NAME}" --region "${AWS_REGION}" >/dev/null 2>&1; then
  aws secretsmanager put-secret-value \
    --secret-id "${GCP_WIF_SECRET_NAME}" \
    --secret-string "file://${CRED_CONFIG}" \
    --region "${AWS_REGION}" >/dev/null
else
  aws secretsmanager create-secret \
    --name "${GCP_WIF_SECRET_NAME}" \
    --secret-string "file://${CRED_CONFIG}" \
    --region "${AWS_REGION}" >/dev/null
fi

echo "WIF ready. Secret: ${GCP_WIF_SECRET_NAME}"

