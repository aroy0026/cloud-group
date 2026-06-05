# Deployment Guide

## 1. AWS

1. Create Cognito User Pool.
2. Create S3 upload bucket with public access blocked.
3. Configure S3 CORS for frontend origin.
4. Create SNS topics for watched tags.
5. Create a GCP service account JSON key in GCP and store it in AWS Secrets Manager as `gcp-firestore-service-account`.
6. Package each Lambda with `aws/lambdas/requirements.txt` and the `common/` folder.
7. Create API Gateway routes:
   - `POST /uploads/presign` -> `presign_upload`
   - `GET /media/{mediaId}` -> `query_api`
   - `POST /query/tags` -> `query_api`
   - `POST /query/species` -> `query_api`
   - `POST /query/thumbnail` -> `query_api`
   - `POST /query/file` -> `query_api`
   - `POST /media/tags/bulk` -> `tag_api`
   - `POST /media/delete` -> `delete_api`
   - `POST /notifications/watch` -> `notification_api`
   - `POST /notifications/unwatch` -> `notification_api`
8. Attach Cognito authorizer to every route.
9. Add S3 ObjectCreated trigger for `uploads/` prefix to `ingest_dispatcher`.

## 2. GCP

1. Enable APIs: Cloud Run, Cloud Build, Artifact Registry, Cloud Storage, Firestore, Pub/Sub, Secret Manager.
2. Create Firestore in Native mode.
3. Create processing Cloud Storage bucket.
4. Create Pub/Sub topic `media-processing`.
5. Create service accounts:
   - `aws-dispatcher-sa`
   - `cloud-run-processor-sa`
6. Copy model files:

```bash
cp ../../AussieEcoLense/model.pt gcp/cloudrun_processor/model.pt
cp ../../AussieEcoLense/mdv5a.pt gcp/cloudrun_processor/mdv5a.pt
cp ../../AussieEcoLense/labels.txt gcp/cloudrun_processor/labels.txt
```

7. Build and deploy Cloud Run:

```bash
cd gcp/cloudrun_processor
gcloud builds submit --tag REGION-docker.pkg.dev/PROJECT/aussie-ecolens/processor:latest
gcloud run deploy aussie-ecolens-processor \
  --image REGION-docker.pkg.dev/PROJECT/aussie-ecolens/processor:latest \
  --region REGION \
  --service-account cloud-run-processor-sa@PROJECT.iam.gserviceaccount.com \
  --memory 8Gi \
  --cpu 2 \
  --timeout 900 \
  --concurrency 1 \
  --set-env-vars GCS_BUCKET=YOUR_BUCKET
```

8. Create Pub/Sub push subscription to Cloud Run `/` endpoint.
9. Set `QUERY_FILE_PROCESSOR_URL` in AWS query Lambda to Cloud Run `/query-file`.

## 3. Frontend

```bash
cd frontend
npm install
npm run build
```

Deploy via AWS Amplify, S3 + CloudFront, or any HTTPS static host.

