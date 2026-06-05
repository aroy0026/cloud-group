# Aussie EcoLens Complete Code Structure

This folder is the clean source-code package for the FIT5225 Aussie EcoLens AWS + GCP HD implementation.

Secrets, generated dependency folders, generated Lambda zips, Terraform state, frontend `.env` files, and large model binaries are intentionally excluded. Recreate generated artifacts with the scripts in this repository.

```text
aussie-ecolens-complete-code/
  README.md
  .env.example
  aws-project-v2.env.example
  .gitignore
  PROJECT_STRUCTURE.md
  MODEL_FILES.md
  scripts_package_lambda.sh
  scripts_package_all_lambdas.sh
  scripts_prepare_models.sh
  scripts_aws_apply.sh
  scripts_gcp_build_and_deploy_cloudrun.sh
  scripts_gcp_first_pass.sh
  scripts_store_gcp_key_in_aws.sh
  scripts_write_frontend_env.sh

  frontend/
    index.html
    package.json
    package-lock.json
    tsconfig.json
    vite.config.ts
    src/
      App.tsx
      main.tsx
      styles.css
      vite-env.d.ts
      lib/
        api.ts
        checksum.ts

  aws/
    infra/
      main.tf
      variables.tf
    lambdas/
      requirements.txt
      common/
        auth.py
        gcp.py
        response.py
        storage.py
      presign_upload/
        handler.py
      ingest_dispatcher/
        handler.py
      query_api/
        handler.py
      tag_api/
        handler.py
      delete_api/
        handler.py
      notification_api/
        handler.py

  gcp/
    infra/
      main.tf
      variables.tf
    cloudrun_processor/
      Dockerfile
      README.md
      requirements.txt
      app.py
      processor.py
      model_adapter.py
      notifier.py
      labels.txt

  shared/
    schema.md

  docs/
    api-contract.md
    deployment.md
    demo-script.md
    packaging-lambdas.md
```

## What Each Part Does

| Path | Purpose |
|---|---|
| `frontend/` | React + Vite UI with Cognito authentication, upload, status, query, tag edit, delete, and notification panels. |
| `frontend/src/lib/api.ts` | Authenticated frontend API client. Adds Cognito bearer token to API Gateway calls and performs direct S3 PUT upload. |
| `frontend/src/lib/checksum.ts` | Browser SHA-256 checksum generation for duplicate detection. |
| `aws/lambdas/common/` | Shared Lambda helpers for Cognito claims, CORS/JSON responses, GCP credentials from AWS Secrets Manager, Firestore/GCS/PubSub clients, signed URLs, and delete helpers. |
| `aws/lambdas/presign_upload/` | `POST /uploads/presign`; creates Firestore checksum reservation and returns a presigned S3 PUT URL. |
| `aws/lambdas/ingest_dispatcher/` | S3 ObjectCreated trigger; validates duplicate checksum, mirrors object to GCP Cloud Storage, writes Firestore status, publishes Pub/Sub job. |
| `aws/lambdas/query_api/` | Query by tag counts, species, thumbnail URL, uploaded query file, and media status. |
| `aws/lambdas/tag_api/` | Bulk manual tag add/remove with `operation=1` add and `operation=0` remove. |
| `aws/lambdas/delete_api/` | Deletes media from S3, GCS, Firestore media, checksum index, and thumbnail index. |
| `aws/lambdas/notification_api/` | Creates/updates SNS email watches and optional internal publish endpoint. |
| `gcp/cloudrun_processor/` | Flask Cloud Run service for Pub/Sub push jobs and temporary query-file detection. |
| `gcp/cloudrun_processor/processor.py` | Generates thumbnails, extracts video frames at one frame per second, creates species-based `classified/<tag>/...` storage copies, runs model adapter, updates Firestore, triggers notifications. |
| `gcp/cloudrun_processor/model_adapter.py` | Loads model/labels from environment-configured paths so model updates do not require source-code changes. |
| `aws/infra/` and `gcp/infra/` | Terraform skeletons for cloud resources. |
| `docs/` | Deployment, API, packaging, and demo notes. |

## Main Runtime Flow

1. Cognito authenticates the user.
2. Frontend computes SHA-256 and calls `POST /uploads/presign`.
3. `presign_upload` blocks duplicates using Firestore `checksums/{sha256}`.
4. Frontend uploads directly to private S3 with the presigned URL.
5. S3 ObjectCreated triggers `ingest_dispatcher`.
6. Dispatcher mirrors the object to GCP Cloud Storage and publishes a Pub/Sub job.
7. Cloud Run processes the media, generates thumbnails/video frame tags, and updates Firestore.
8. API Gateway + Lambda query/edit/delete/notify endpoints serve the protected UI.

## Rebuild Generated Artifacts

```bash
cd "/Users/alphinroy/Projects/cloud repotr/aussie-ecolens-complete-code"

# Frontend dependencies and local demo
cd frontend
npm install
npm run dev

# Lambda zip packages
cd ..
./scripts_package_all_lambdas.sh

# Cloud Run image and GCP Terraform deploy
export GCP_PROJECT_ID="YOUR_PROJECT_ID"
export GCP_REGION="australia-southeast1"
export GCP_PROCESSING_BUCKET="YOUR_PROCESSING_BUCKET"
./scripts_gcp_build_and_deploy_cloudrun.sh
```
