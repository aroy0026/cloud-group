# Cloud Run Processor

This service receives Pub/Sub push messages from the AWS S3 dispatcher and processes media.

## Endpoints

- `POST /`: Pub/Sub push endpoint for permanent uploaded media.
- `POST /query-file`: temporary query-file classification; does not write a media record.
- `GET /health`: health check.

## Deploy

Copy model files into this folder before building, or change the Dockerfile to copy them from your build context.

```bash
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

