# GCP Setup — ML Service
## EcoLens — Day 1, Phase 5

---

## GCP Config Reference

```
Project ID:        ecolens-savio-v2
Project Number:    810236742778
Billing Account:   01A615-2371BD-151128

GCS Bucket:        ecolens-media-savio-v2
Bucket Region:     australia-southeast2 (Melbourne)
Folders:           uploads/ thumbnails/ models/

Service Account:   ecolens-ml-sa@ecolens-savio-v2.iam.gserviceaccount.com
SA Roles:          roles/storage.objectViewer
                   roles/logging.logWriter
                   roles/run.invoker

Cloud Run Service: ecolens-ml-service
Service URL:       https://ecolens-ml-service-810236742778.australia-southeast2.run.app
Tag Endpoint:      POST /tag
Health Endpoint:   GET /health
Region:            australia-southeast2
Memory:            8Gi
CPU:               4
Timeout:           540s
```

---

## What This Does

GCP hosts the ML inference service using Cloud Run. The service runs two
models in sequence:
1. **MegaDetector** (`mdv5a.pt`) — detects animals in the image and returns bounding boxes
2. **SpeciesNet** (`model.pt`) — classifies each detected animal into one of 46 Australian wildlife species

The service is triggered by the AWS Upload Lambda after a file is stored
in S3. It downloads the image from S3, runs ML inference, and writes the
detected tags back to DynamoDB.

---

## ML Pipeline Flow

```
Upload Lambda → POST /tag {file_id, s3_key}
     → Download image from S3 (ap-southeast-4)
     → MegaDetector finds animals + bounding boxes
     → Crop each detected animal
     → SpeciesNet classifies each crop
     → Tags written to DynamoDB
     → Response returned to Lambda
```

---

## Step 1 — Create GCP Project

```powershell
gcloud projects create ecolens-savio-v2 --name="EcoLens V2"
gcloud config set project ecolens-savio-v2
```

---

## Step 2 — Link Billing Account

```powershell
gcloud billing projects link ecolens-savio-v2 --billing-account=01A615-2371BD-151128
```

---

## Step 3 — Enable Required APIs

```powershell
gcloud services enable run.googleapis.com storage.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project ecolens-savio-v2
```

---

## Step 4 — Create GCS Bucket

```powershell
gcloud storage buckets create gs://ecolens-media-savio-v2 `
  --project ecolens-savio-v2 `
  --location australia-southeast2 `
  --uniform-bucket-level-access
```

---

## Step 5 — Upload ML Models

```powershell
gcloud storage cp "PATH_TO_MODELS\mdv5a.pt" gs://ecolens-media-savio-v2/models/
gcloud storage cp "PATH_TO_MODELS\model.pt" gs://ecolens-media-savio-v2/models/
gcloud storage cp "PATH_TO_MODELS\labels.txt" gs://ecolens-media-savio-v2/models/
gcloud storage cp "PATH_TO_MODELS\config.yaml" gs://ecolens-media-savio-v2/models/
```

---

## Step 6 — Create Service Account

```powershell
gcloud iam service-accounts create ecolens-ml-sa `
  --display-name="EcoLens ML Service Account" `
  --project ecolens-savio-v2
```

---

## Step 7 — Grant Minimal Permissions

```powershell
gcloud projects add-iam-policy-binding ecolens-savio-v2 `
  --member="serviceAccount:ecolens-ml-sa@ecolens-savio-v2.iam.gserviceaccount.com" `
  --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding ecolens-savio-v2 `
  --member="serviceAccount:ecolens-ml-sa@ecolens-savio-v2.iam.gserviceaccount.com" `
  --role="roles/logging.logWriter"

gcloud projects add-iam-policy-binding ecolens-savio-v2 `
  --member="serviceAccount:ecolens-ml-sa@ecolens-savio-v2.iam.gserviceaccount.com" `
  --role="roles/run.invoker"
```

---

## Step 8 — Deploy Cloud Run Service

```powershell
gcloud run deploy ecolens-ml-service `
  --source . `
  --region australia-southeast2 `
  --platform managed `
  --allow-unauthenticated `
  --memory 8Gi `
  --cpu 4 `
  --timeout 540 `
  --service-account ecolens-ml-sa@ecolens-savio-v2.iam.gserviceaccount.com `
  --set-env-vars "AWS_ACCESS_KEY_ID=YOUR_KEY,AWS_SECRET_ACCESS_KEY=YOUR_SECRET,AWS_DEFAULT_REGION=ap-southeast-4" `
  --project ecolens-savio-v2
```

> Run from inside `ecolens/backend/gcp/ml-service/` directory.
> Replace YOUR_KEY and YOUR_SECRET with xav_08 IAM user credentials.

---

## Verification

```powershell
Invoke-RestMethod `
  -Uri "https://ecolens-ml-service-810236742778.australia-southeast2.run.app/health" `
  -Method GET
```

Expected: `{"status": "healthy"}`

---

## Updating AWS Credentials

The xav_08 credentials are long-lived (personal account) so they don't
expire like AWS Academy credentials. No rotation needed unless you
regenerate the access key.

To update credentials if needed:
```powershell
gcloud run services update ecolens-ml-service `
  --region australia-southeast2 `
  --set-env-vars "AWS_ACCESS_KEY_ID=NEW_KEY,AWS_SECRET_ACCESS_KEY=NEW_SECRET,AWS_DEFAULT_REGION=ap-southeast-4" `
  --project ecolens-savio-v2
```

---

## Checklist

```
☑ GCP project created (ecolens-savio-v2)
☑ Billing account linked
☑ Required APIs enabled
☑ GCS bucket created (ecolens-media-savio-v2) in australia-southeast2
☑ ML models uploaded (mdv5a.pt, model.pt, labels.txt, config.yaml)
☑ Service account created (ecolens-ml-sa) with minimal permissions
☑ Cloud Run service deployed (ecolens-ml-service)
☑ Health check passing
```
