# Aussie EcoLens Platform

AWS + GCP multi-cloud serverless wildlife media platform for FIT5225 A2.

## Recommended Architecture

- AWS Cognito: sign-up, email verification, sign-in, sign-out.
- AWS API Gateway + Lambda: protected REST APIs.
- AWS S3: browser upload ingress with presigned URLs.
- AWS Lambda dispatcher: mirrors uploads to GCP and queues jobs.
- GCP Pub/Sub: processing queue.
- GCP Cloud Run: ML processing, image thumbnails, video frame extraction.
- GCP Cloud Storage: mirrored originals, thumbnails, temporary query files.
- GCP Firestore: media metadata, checksum index, tags, thumbnails, watches.
- AWS SNS: tag-based email notifications.

## Project Layout

```text
frontend/                 React/Vite UI
aws/lambdas/              Python Lambda handlers
aws/infra/                Terraform skeleton for AWS resources
gcp/cloudrun_processor/   Cloud Run ML service
gcp/infra/                Terraform skeleton for GCP resources
shared/                   Shared schema notes
docs/                     Demo and deployment notes
```

## What Is Complete

This repository contains complete deployable source templates for:

- Cognito-protected API handlers.
- Presigned upload + checksum deduplication.
- S3 upload dispatcher to GCP.
- Firestore metadata operations.
- Query by tags/counts/species/thumbnail URL.
- Query-by-file endpoint that does not permanently store the query file.
- Bulk tag add/remove.
- Delete from storage and Firestore.
- SNS notification subscription/watch API.
- Cloud Run media processor with image thumbnails, video 1 fps extraction, and model adapter.
- React frontend with auth, upload, query, tag edit, delete, and notification screens.

You still need to create real AWS/GCP resources and fill environment variables. Cloud IDs, bucket names, Cognito IDs, and secrets cannot be guessed in code.

## Fast Start

1. Copy `.env.example` to the relevant environment files.
2. Create AWS Cognito, S3, API Gateway, Lambda, SNS, and Secrets Manager resources.
3. Create GCP Firestore, Cloud Storage, Pub/Sub, Artifact Registry, and Cloud Run resources.
4. Store the GCP service account JSON in AWS Secrets Manager.
5. Deploy Lambdas with their requirements.
6. Build and deploy the Cloud Run container.
7. Deploy the frontend and set API/Cognito env vars.
8. Use `../test_images` for demo uploads.

See [docs/deployment.md](docs/deployment.md) and [docs/demo-script.md](docs/demo-script.md).

