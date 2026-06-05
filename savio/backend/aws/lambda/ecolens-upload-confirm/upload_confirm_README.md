# ecolens-upload-confirm
## EcoLens Lambda Function

---

## What This Does

Second step of the upload flow. Called after the browser has
successfully uploaded the file directly to S3 via the presigned URL.
Sets DynamoDB status to `processing` then immediately invokes
`ecolens-ml-trigger` asynchronously and returns to the frontend.
ML processing happens in the background.

---

## Trigger

```
API Gateway: POST /upload/confirm
```

---

## IAM Role

```
ecolens-upload-role
```

---

## Request Body

```json
{
  "mediaId": "uuid-here",
  "s3Key": "uploads/images/uuid_filename.jpg"
}
```

---

## Response

```json
{
  "mediaId": "uuid-here",
  "status": "processing",
  "fileUrl": "https://ecolens-media-savio-melbourne.s3.ap-southeast-4.amazonaws.com/..."
}
```

---

## Flow

```
Frontend → POST /upload/confirm {mediaId, s3Key}
  → Update DynamoDB status: QUEUED → processing
  → Invoke ecolens-ml-trigger Lambda ASYNC (InvocationType=Event)
      (fire and forget — does not wait for ML result)
  → Return immediately: {status: processing}

Background (ecolens-ml-trigger):
  → Calls GCP ML service
  → Updates DynamoDB with tags + thumbnail + status ready
```

> Frontend uses the Refresh button on the upload page to poll for
> status changes from processing → ready.

---

## Why Async?

API Gateway has a hard 29 second timeout. Video ML processing (1
frame/sec × ML inference) takes several minutes. Async invocation
allows the confirm Lambda to return in <1 second while ML runs in
the background for up to 15 minutes.

---

## Key Config

```python
TABLE_NAME  = 'ecolens-media'
BUCKET_NAME = 'ecolens-media-savio-melbourne'
REGION      = 'ap-southeast-4'
```

---

## Deploy / Update

```powershell
cd ecolens/backend/aws/lambda/ecolens-upload-confirm

Compress-Archive -Path lambda_function.py -DestinationPath function.zip -Force

# First deploy
aws lambda create-function `
  --function-name ecolens-upload-confirm `
  --runtime python3.12 `
  --role arn:aws:iam::686112929724:role/ecolens-upload-role `
  --handler lambda_function.lambda_handler `
  --zip-file fileb://function.zip `
  --timeout 30 `
  --memory-size 256 `
  --region ap-southeast-4

# Update existing
aws lambda update-function-code `
  --function-name ecolens-upload-confirm `
  --zip-file fileb://function.zip `
  --region ap-southeast-4
```

---

## API Gateway Integration

```
Resource:    /upload/confirm
Method:      POST
Type:        AWS_PROXY
Resource ID: 45338n
API ID:      g4raf95x4b
```

---

## Checklist

```
☑ Lambda created (ecolens-upload-confirm)
☑ Runtime: Python 3.12
☑ Role: ecolens-upload-role
☑ Timeout: 30s (returns in <1s now)
☑ Memory: 256MB
☑ API Gateway POST /upload/confirm connected
☑ DynamoDB status set to processing immediately
☑ ecolens-ml-trigger invoked asynchronously
☑ Returns without waiting for ML result
☑ No 504 timeout errors
```
