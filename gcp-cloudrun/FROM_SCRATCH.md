# GCP Cloud Run ML Processor From Scratch

This is the complete handoff guide for another developer to run or redeploy the Aussie EcoLens Cloud Run ML tagging service.

## 1. What This Service Does

This service receives media bytes and returns wildlife tags.

In the current deployed architecture, AWS Lambda sends images and extracted video frames to:

```text
POST /query-file
```

The service:

1. Loads `model.pt`.
2. Loads `labels.txt`.
3. Converts the image/frame to RGB.
4. Resizes to `480 x 480`.
5. Runs the PyTorch model.
6. Applies `CONFIDENCE_THRESHOLD`.
7. Returns tags as JSON.

Example response:

```json
{
  "tags": {
    "canis_dingo": 1
  }
}
```

## 2. Required Files

These files must exist in this folder:

```text
gcp-cloudrun/
  app.py
  model_adapter.py
  processor.py
  notifier.py
  requirements.txt
  Dockerfile
  labels.txt
  deploy.sh
  .env.example
  MODEL_FILES.md
  AWS_LAMBDA_INTEGRATION.md
  local_query_test.py
  infra/
    main.tf
    variables.tf
```

Large model files are also required before building:

```text
model.pt
mdv5a.pt
```

They are intentionally not duplicated in Git. Copy them from the existing model package:

```bash
cp ../aussie-ecolens-complete-code/gcp/cloudrun_processor/model.pt ./model.pt
cp ../aussie-ecolens-complete-code/gcp/cloudrun_processor/mdv5a.pt ./mdv5a.pt
```

## 3. Required Local Tools

Install:

- Python 3.12
- Docker
- Google Cloud CLI: `gcloud`
- Optional for local testing: `curl`, `jq`

Check:

```bash
python3 --version
docker --version
gcloud --version
```

## 4. Required GCP Resources

Recommended project/region:

```text
Project: project-b70b0656-b022-41bd-bc6
Region: australia-southeast1
Service: aussie-ecolens-processor
Artifact Registry repository: aussie-ecolens
Processing bucket: aussie-ecolens-processing-project-b70b0656-b022-41bd-bc6
```

Enable APIs:

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  iam.googleapis.com \
  sts.googleapis.com \
  iamcredentials.googleapis.com \
  storage.googleapis.com \
  firestore.googleapis.com \
  --project project-b70b0656-b022-41bd-bc6
```

Create Artifact Registry repository if it does not exist:

```bash
gcloud artifacts repositories create aussie-ecolens \
  --repository-format=docker \
  --location=australia-southeast1 \
  --description="Aussie EcoLens containers" \
  --project project-b70b0656-b022-41bd-bc6
```

Create or confirm the GCS bucket:

```bash
gcloud storage buckets create gs://aussie-ecolens-processing-project-b70b0656-b022-41bd-bc6 \
  --location=australia-southeast1 \
  --project project-b70b0656-b022-41bd-bc6
```

## 5. Environment Variables

Cloud Run should have:

```text
GCS_BUCKET=aussie-ecolens-processing-project-b70b0656-b022-41bd-bc6
CONFIDENCE_THRESHOLD=0.20
MODEL_PATH=/app/model.pt
LABELS_PATH=/app/labels.txt
```

`CONFIDENCE_THRESHOLD=0.20` is the current reasonable threshold:

- `0.05` is very permissive and noisy.
- `0.35` can miss uncertain wildlife detections.
- `0.20` is a practical midpoint for assignment demo tagging.

## 6. Local Development

Create a virtual environment:

```bash
cd gcp-cloudrun
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy model files:

```bash
cp ../aussie-ecolens-complete-code/gcp/cloudrun_processor/model.pt ./model.pt
cp ../aussie-ecolens-complete-code/gcp/cloudrun_processor/mdv5a.pt ./mdv5a.pt
```

Run locally:

```bash
export GCS_BUCKET=aussie-ecolens-processing-project-b70b0656-b022-41bd-bc6
export MODEL_PATH=./model.pt
export LABELS_PATH=./labels.txt
export CONFIDENCE_THRESHOLD=0.20
flask --app app run --host 0.0.0.0 --port 8080
```

Health check:

```bash
curl http://localhost:8080/health
```

Query-file test:

```bash
python local_query_test.py http://localhost:8080/query-file ../test_images/Alectura_lathami_1.JPG
```

## 7. Docker Build Locally

Copy model files first:

```bash
cp ../aussie-ecolens-complete-code/gcp/cloudrun_processor/model.pt ./model.pt
cp ../aussie-ecolens-complete-code/gcp/cloudrun_processor/mdv5a.pt ./mdv5a.pt
```

Build:

```bash
docker build -t aussie-ecolens-processor:local .
```

Run:

```bash
docker run --rm -p 8080:8080 \
  -e GCS_BUCKET=aussie-ecolens-processing-project-b70b0656-b022-41bd-bc6 \
  -e CONFIDENCE_THRESHOLD=0.20 \
  aussie-ecolens-processor:local
```

Test:

```bash
curl http://localhost:8080/health
python local_query_test.py http://localhost:8080/query-file ../test_images/Alectura_lathami_1.JPG
```

## 8. Deploy To Cloud Run

Login:

```bash
gcloud auth login
gcloud config set project project-b70b0656-b022-41bd-bc6
```

Deploy:

```bash
cd gcp-cloudrun
./deploy.sh
```

The service is deployed private with:

```text
--no-allow-unauthenticated
```

This is intentional. AWS Lambda uses Workload Identity Federation to call it.

## 9. Direct Authenticated Cloud Run Test

Get the service URL:

```bash
gcloud run services describe aussie-ecolens-processor \
  --region australia-southeast1 \
  --project project-b70b0656-b022-41bd-bc6 \
  --format='value(status.url)'
```

Health test with identity token:

```bash
SERVICE_URL="$(gcloud run services describe aussie-ecolens-processor \
  --region australia-southeast1 \
  --project project-b70b0656-b022-41bd-bc6 \
  --format='value(status.url)')"

TOKEN="$(gcloud auth print-identity-token)"

curl -H "Authorization: Bearer ${TOKEN}" "${SERVICE_URL}/health"
```

Query-file test:

```bash
curl -X POST "${SERVICE_URL}/query-file" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: image/jpeg" \
  --data-binary @../test_images/Alectura_lathami_1.JPG
```

## 10. AWS Lambda Connection Checklist

After Cloud Run deploy, update Lambda env vars:

```text
QUERY_FILE_PROCESSOR_URL=<SERVICE_URL>/query-file
QUERY_FILE_PROCESSOR_TIMEOUT=120
CLOUD_RUN_AUDIENCE=<SERVICE_URL>
GCP_WIF_CREDENTIAL_CONFIG_SECRET=ecolens-gcp-wif-credential-config
GCP_SERVICE_ACCOUNT_EMAIL=aws-ecolens-invoker@project-b70b0656-b022-41bd-bc6.iam.gserviceaccount.com
```

See `AWS_LAMBDA_INTEGRATION.md` for Workload Identity Federation details.

## 11. Common Problems

### Cloud Run returns 403

Cause: caller does not have `roles/run.invoker`.

Fix:

```bash
gcloud run services add-iam-policy-binding aussie-ecolens-processor \
  --region australia-southeast1 \
  --project project-b70b0656-b022-41bd-bc6 \
  --member "serviceAccount:aws-ecolens-invoker@project-b70b0656-b022-41bd-bc6.iam.gserviceaccount.com" \
  --role roles/run.invoker
```

### Docker build fails because model files are missing

Copy:

```bash
cp ../aussie-ecolens-complete-code/gcp/cloudrun_processor/model.pt ./model.pt
cp ../aussie-ecolens-complete-code/gcp/cloudrun_processor/mdv5a.pt ./mdv5a.pt
```

### Too many false positive tags

Raise:

```text
CONFIDENCE_THRESHOLD=0.25
```

### Too few tags

Lower:

```text
CONFIDENCE_THRESHOLD=0.15
```

### Lambda times out on video

Keep frame count capped on Lambda:

```text
VIDEO_MAX_FRAMES=12
QUERY_FILE_PROCESSOR_TIMEOUT=120
```

## 12. File Ownership Summary

Use this folder for GCP Cloud Run only.

Use `../aws/lambda/` for AWS Lambda code.

Use `../dynamo-db/` for DynamoDB table setup and schema notes.

Use `../frontend/` for the React UI.

