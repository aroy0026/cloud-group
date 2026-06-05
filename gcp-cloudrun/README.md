# GCP Cloud Run ML Processor

This folder contains the GCP Cloud Run service used by Aussie EcoLens for ML tagging.

## Live Service

- Project: `project-b70b0656-b022-41bd-bc6`
- Region: `australia-southeast1`
- Service: `aussie-ecolens-processor`
- Private URL: `https://aussie-ecolens-processor-665098755528.australia-southeast1.run.app`
- AWS access: private invocation through Workload Identity Federation from the Lambda execution role.

## Files

- `app.py`: Flask HTTP entrypoint.
- `model_adapter.py`: loads the PyTorch model and applies confidence threshold filtering.
- `processor.py`: media processing helpers for GCS/Firestore-oriented processing and query-file tagging.
- `notifier.py`: notification helper.
- `Dockerfile`: Cloud Run container build.
- `requirements.txt`: Python dependencies.
- `labels.txt`: model label mapping.
- `infra/`: Terraform files for the Cloud Run/GCP side.

## Endpoints

- `GET /health`: health check.
- `POST /query-file`: temporary ML tagging for a query image/frame. This is the endpoint called by AWS Lambda.
- `POST /`: Pub/Sub push style processor endpoint retained from the complete architecture package.

## Confidence Threshold

The service reads:

```text
CONFIDENCE_THRESHOLD
```

Current source fallback is `0.20`, which is a reasonable assignment/demo threshold: stricter than `0.05`, less conservative than `0.35`.

## Model Files

The model weight files are intentionally not duplicated in this folder because they are large. Before building this folder directly, copy:

```bash
cp ../aussie-ecolens-complete-code/gcp/cloudrun_processor/model.pt ./model.pt
cp ../aussie-ecolens-complete-code/gcp/cloudrun_processor/mdv5a.pt ./mdv5a.pt
```

## Deploy

Use `deploy.sh` after confirming `gcloud` is logged in and the project is selected.

