# ecolens-thumbnail-query
## EcoLens Lambda Function

---

## What This Does

Finds the original full-size file associated with a given thumbnail URL.
Scans DynamoDB for a record where `thumbnail_url` matches the provided
URL and returns the full file details including a presigned download URL.

---

## Trigger

```
API Gateway: POST /query/thumbnail
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
  "thumbnailUrl": "https://ecolens-media-savio-melbourne.s3.ap-southeast-4.amazonaws.com/thumbnails/uuid_filename.JPG"
}
```

> Also accepts presigned URLs — query params are stripped before matching.

---

## Response

```json
{
  "fullImageUrl": "https://presigned-s3-url-for-original...",
  "canonicalFullImageUrl": "https://ecolens-media-savio-melbourne.s3.ap-southeast-4.amazonaws.com/uploads/images/uuid_filename.JPG",
  "mediaId": "uuid-here",
  "originalName": "Sus_scrofa_1.JPG",
  "tags": { "Sus_scrofa": 1 },
  "thumbnailUrl": "https://presigned-s3-url-for-thumbnail...",
  "status": "ready"
}
```

---

## Flow

```
Frontend → POST /query/thumbnail {thumbnailUrl}
  → Normalize URL (strip presigned query params)
  → Scan DynamoDB table (with pagination)
  → Match thumbnail_url field (normalized comparison)
  → Generate presigned URLs for full image and thumbnail
  → Return file details
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
cd ecolens/backend/aws/lambda/ecolens-thumbnail-query

Compress-Archive -Path lambda_function.py -DestinationPath function.zip -Force

# First deploy
aws lambda create-function `
  --function-name ecolens-thumbnail-query `
  --runtime python3.12 `
  --role arn:aws:iam::686112929724:role/ecolens-query-role `
  --handler lambda_function.lambda_handler `
  --zip-file fileb://function.zip `
  --timeout 30 `
  --memory-size 256 `
  --region ap-southeast-4

# Update existing
aws lambda update-function-code `
  --function-name ecolens-thumbnail-query `
  --zip-file fileb://function.zip `
  --region ap-southeast-4
```

---

## API Gateway Integration

```
Resource:    /query/thumbnail
Method:      POST
Type:        AWS_PROXY
Resource ID: ywk7uq
API ID:      g4raf95x4b
```

---

## Verification

```powershell
$body = '{"thumbnailUrl": "https://ecolens-media-savio-melbourne.s3.ap-southeast-4.amazonaws.com/thumbnails/e7516d71-9165-4a84-a173-576f055d4b38_Sus_scrofa_1.JPG"}'

Invoke-RestMethod `
  -Uri "https://g4raf95x4b.execute-api.ap-southeast-4.amazonaws.com/dev/query/thumbnail" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

Expected: `fullImageUrl`, `mediaId`, `tags` returned ✅

---

## Checklist

```
☑ Lambda created (ecolens-thumbnail-query)
☑ Runtime: Python 3.12
☑ Role: ecolens-query-role
☑ Timeout: 30s
☑ Memory: 256MB
☑ API Gateway POST /query/thumbnail connected
☑ URL normalization (strips presigned query params)
☑ Presigned URLs generated for full image and thumbnail
☑ Frontend search by thumbnail URL working
```
