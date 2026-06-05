# ecolens-query-file-presign
## EcoLens Lambda Function

---

## What This Does

First step of the file query flow. Generates a presigned S3 URL so the
browser can upload the query file directly to S3 temp-query/ folder,
bypassing the 10MB API Gateway payload limit.

---

## Trigger

```
API Gateway: POST /query/file/presign
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
  "filename": "koala-query.jpg",
  "contentType": "image/jpeg"
}
```

---

## Response

```json
{
  "uploadUrl": "https://ecolens-media-savio-melbourne.s3.ap-southeast-4.amazonaws.com/temp-query/uuid.jpg?...",
  "s3Key": "temp-query/uuid.jpg"
}
```

---

## Flow

```
Frontend → POST /query/file/presign {filename, contentType}
  → Generate UUID temp file key under temp-query/
  → Generate presigned S3 PUT URL (5 min expiry)
  → Return uploadUrl + s3Key

Frontend → PUT file directly to S3 via uploadUrl
Frontend → POST /query/file {s3Key} → ecolens-file-query Lambda
```

---

## Key Config

```python
BUCKET_NAME = 'ecolens-media-savio-melbourne'
REGION      = 'ap-southeast-4'
EXPIRY      = 300  # 5 minutes
```

---

## Deploy / Update

```powershell
cd ecolens/backend/aws/lambda/ecolens-query-file-presign

Compress-Archive -Path lambda_function.py -DestinationPath function.zip -Force

# First deploy
aws lambda create-function `
  --function-name ecolens-query-file-presign `
  --runtime python3.12 `
  --role arn:aws:iam::686112929724:role/ecolens-query-role `
  --handler lambda_function.lambda_handler `
  --zip-file fileb://function.zip `
  --timeout 30 `
  --memory-size 256 `
  --region ap-southeast-4

# Update existing
aws lambda update-function-code `
  --function-name ecolens-query-file-presign `
  --zip-file fileb://function.zip `
  --region ap-southeast-4
```

---

## API Gateway Integration

```
Resource:    /query/file/presign
Method:      POST
Type:        AWS_PROXY
Resource ID: 8xk7ab
API ID:      g4raf95x4b
```

---

## Checklist

```
☑ Lambda created (ecolens-query-file-presign)
☑ Runtime: Python 3.12
☑ Role: ecolens-query-role
☑ Timeout: 30s
☑ Memory: 256MB
☑ API Gateway POST /query/file/presign connected
☑ CORS configured on resource
☑ Presigned URL generation working
☑ Supports files of any size
```
