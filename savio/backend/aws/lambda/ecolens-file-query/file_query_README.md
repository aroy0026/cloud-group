# ecolens-file-query
## EcoLens Lambda Function

---

## What This Does

Second step of the file query flow. Receives an S3 key for a temp file
already uploaded directly to S3, runs ML inference on it to detect
species, searches DynamoDB for matching files, then deletes the temp file.

---

## Trigger

```
API Gateway: POST /query/file
```

---

## IAM Role

```
ecolens-query-role
```

---

## Request Body

```json
{
  "s3Key": "temp-query/uuid.jpg"
}
```

---

## Response

```json
{
  "detectedTags": { "Felis_catus": 1 },
  "results": [
    {
      "mediaId": "uuid-here",
      "originalName": "Felis_catus_1.JPG",
      "tags": { "Felis_catus": 1 },
      "fullUrl": "https://presigned-url...",
      "thumbnailUrl": "https://presigned-url...",
      "status": "ready"
    }
  ],
  "count": 1
}
```

---

## Flow

```
Frontend → POST /query/file {s3Key}
  → POST GCP Cloud Run /tag with DO-NOT-SAVE- prefix file_id
      → ML detects species tags (DynamoDB NOT updated)
  → Search DynamoDB for files with ANY matching species (OR logic)
  → Delete temp file from S3
  → Return detected tags + matching files
```

> Note: Uses OR logic unlike tag query which uses AND logic.
> The DO-NOT-SAVE- prefix tells GCP ML service to skip DynamoDB update.
> Always called after ecolens-query-file-presign.

---

## Key Config

```python
BUCKET_NAME = 'ecolens-media-savio-melbourne'
TABLE_NAME  = 'ecolens-media'
GCP_ML_URL  = 'https://ecolens-ml-service-810236742778.australia-southeast2.run.app/tag'
REGION      = 'ap-southeast-4'
```

---

## Deploy / Update

```powershell
cd ecolens/backend/aws/lambda/ecolens-file-query

Compress-Archive -Path lambda_function.py -DestinationPath function.zip -Force

# First deploy
aws lambda create-function `
  --function-name ecolens-file-query `
  --runtime python3.12 `
  --role arn:aws:iam::686112929724:role/ecolens-query-role `
  --handler lambda_function.lambda_handler `
  --zip-file fileb://function.zip `
  --timeout 600 `
  --memory-size 256 `
  --region ap-southeast-4

# Update existing
aws lambda update-function-code `
  --function-name ecolens-file-query `
  --zip-file fileb://function.zip `
  --region ap-southeast-4
```

---

## API Gateway Integration

```
Resource:    /query/file
Method:      POST
Type:        AWS_PROXY
Resource ID: pvwrcf
API ID:      g4raf95x4b
```

---

## Checklist

```
☑ Lambda created (ecolens-file-query)
☑ Runtime: Python 3.12
☑ Role: ecolens-query-role
☑ Timeout: 600s
☑ Memory: 256MB
☑ API Gateway POST /query/file connected
☑ Accepts s3Key (not raw binary)
☑ DO-NOT-SAVE prefix prevents DynamoDB update
☑ OR logic for species matching
☑ Temp file cleanup after processing
☑ Works with files of any size
```
