# GCP ML Service — Cloud Run
## EcoLens — ecolens-ml-service

---

## Service Config

```
Project:      ecolens-savio-v2
Service:      ecolens-ml-service
Region:       australia-southeast2 (Melbourne)
URL:          https://ecolens-ml-service-810236742778.australia-southeast2.run.app
Memory:       8Gi
CPU:          4
Timeout:      540s
Tag Endpoint: POST /tag
Health:       GET /health
```

---

## What This Does

GCP Cloud Run ML inference service. Receives file references from AWS
Lambda, downloads the file from S3, runs two ML models in sequence,
and returns detected species tags.

For videos, also extracts frames at 1 frame per second, runs ML on
each frame, combines results, and returns the first frame as a base64
thumbnail.

---

## ML Pipeline

### Image Flow
```
POST /tag {file_id, s3_key}
  → Download image from S3
  → MegaDetector: detect animals + bounding boxes
  → Crop each detection
  → SpeciesNet: classify each crop
  → Return {tags: {species: count}}
```

### Video Flow
```
POST /tag {file_id, s3_key}
  → Download video from S3
  → OpenCV: extract 1 frame per second
  → Frame 1 → base64 JPEG thumbnail
  → Each frame → MegaDetector + SpeciesNet
  → Combine: MAX count per species across all frames
  → Return {tags: {species: max_count}, thumbnail_base64, thumbnail_content_type}
```

---

## Models

| Model | File | Size | Purpose |
|---|---|---|---|
| MegaDetector | mdv5a.pt | 280MB | Detect animals in image |
| SpeciesNet | model.pt | 211MB | Classify detected species |

Models are stored in GCS `ecolens-media-savio-v2/models/` and
downloaded to `/tmp/models/` on first request. Subsequent requests
reuse cached models (container stays warm).

---

## Supported Species (46 classes)

Australian wildlife including: Macropus_giganteus, Vombatus_ursinus,
Felis_catus, Canis_familiaris, Sus_scrofa, Trichosurus_vulpecula,
and 40 more species.

---

## Dependencies

```
flask, gunicorn          — web server
torch, torchvision       — ML inference
Pillow                   — image processing
opencv-python-headless   — video frame extraction
boto3                    — S3 + DynamoDB access
google-cloud-storage     — GCS model download
megadetector             — animal detection
```

---

## Deployment

```powershell
cd ecolens/backend/gcp/ml-service

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

> Run from inside ml-service/ directory.
> Deployment takes 5-10 minutes (builds Docker image).

---

## Updating AWS Credentials

```powershell
gcloud run services update ecolens-ml-service `
  --region australia-southeast2 `
  --set-env-vars "AWS_ACCESS_KEY_ID=NEW_KEY,AWS_SECRET_ACCESS_KEY=NEW_SECRET,AWS_DEFAULT_REGION=ap-southeast-4" `
  --project ecolens-savio-v2
```

---

## Cold Start

First request after idle period loads models from GCS (~2-3 minutes).
Subsequent requests are fast as models stay in memory.

---

## Verification

```powershell
# Health check
Invoke-RestMethod `
  -Uri "https://ecolens-ml-service-810236742778.australia-southeast2.run.app/health" `
  -Method GET

# Image test
$body = '{"file_id": "test-001", "s3_key": "uploads/images/your_image.jpg"}'
Invoke-RestMethod `
  -Uri "https://ecolens-ml-service-810236742778.australia-southeast2.run.app/tag" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

---

## Checklist

```
☑ GCP project created (ecolens-savio-v2)
☑ Cloud Run service deployed (ecolens-ml-service)
☑ Service account with minimal permissions
☑ ML models uploaded to GCS
☑ Image ML pipeline working
☑ Video frame extraction working (1 frame/sec using OpenCV)
☑ Video thumbnail returned as base64
☑ MAX aggregation across frames
☑ DO-NOT-SAVE prefix skips DynamoDB update (for query-by-file)
☑ Health check passing
```
