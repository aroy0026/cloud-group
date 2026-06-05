# ecolens-upload-presign
## EcoLens Lambda Function

---

## What This Does

First step of the two-step upload flow. Checks for duplicate files using
a SHA-256 checksum, then generates a presigned S3 URL for direct
browser-to-S3 upload — bypassing the 10MB API Gateway payload limit.

---

## Trigger

```
API Gateway: POST /upload/presign
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
  "filename": "koala.jpg",
  "contentType": "image/jpeg",
  "size": 338257,
  "sha256": "abc123..."
}
```

---

## Response — New File

```json
{
  "duplicate": false,
  "mediaId": "uuid-here",
  "uploadUrl": "https://ecolens-media-savio-melbourne.s3.ap-southeast-4.amazonaws.com/...",
  "s3Key": "uploads/images/uuid_filename.jpg"
}
```

## Response — Duplicate File

```json
{
  "duplicate": true,
  "existingMediaId": "uuid-of-existing-file"
}
```

---

## Flow

```
Frontend → POST /upload/presign
  → Check checksum-index GSI for duplicate
  → If duplicate: return existingMediaId
  → If new: generate UUID, create DynamoDB record (status: QUEUED)
  → Generate presigned S3 PUT URL (1 hour expiry)
  → Return uploadUrl + mediaId + s3Key to frontend
```

---

## Key Config

```python
BUCKET_NAME = 'ecolens-media-savio-melbourne'
TABLE_NAME  = 'ecolens-media'
REGION      = 'ap-southeast-4'
```

---

## Deploy / Update

```powershell
cd ecolens/backend/aws/lambda/ecolens-upload-presign

Compress-Archive -Path lambda_function.py -DestinationPath function.zip -Force

# First deploy
aws lambda create-function `
  --function-name ecolens-upload-presign `
  --runtime python3.12 `
  --role arn:aws:iam::686112929724:role/ecolens-upload-role `
  --handler lambda_function.lambda_handler `
  --zip-file fileb://function.zip `
  --timeout 30 `
  --memory-size 256 `
  --region ap-southeast-4

# Update existing
aws lambda update-function-code `
  --function-name ecolens-upload-presign `
  --zip-file fileb://function.zip `
  --region ap-southeast-4
```

---

## API Gateway Integration

```
Resource:   /upload/presign
Method:     POST
Type:       AWS_PROXY
Resource ID: wsr5ar
API ID:     g4raf95x4b
```

---

## Verification

```powershell
$body = '{"filename": "test.jpg", "contentType": "image/jpeg", "size": 12345, "sha256": "testchecksum123"}'

Invoke-RestMethod `
  -Uri "https://g4raf95x4b.execute-api.ap-southeast-4.amazonaws.com/dev/upload/presign" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

Expected: `duplicate: false`, `mediaId` and `uploadUrl` returned ✅

---

## Checklist

```
☑ Lambda created (ecolens-upload-presign)
☑ Runtime: Python 3.12
☑ Role: ecolens-upload-role
☑ Timeout: 30s
☑ Memory: 256MB
☑ API Gateway POST /upload/presign connected
☑ S3 regional endpoint configured
☑ Duplicate detection working
☑ Presigned URL generation working
```
