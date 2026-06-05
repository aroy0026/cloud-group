# ecolens-query
## EcoLens Lambda Function

---

## What This Does

Searches DynamoDB for media files matching specified species tags with
minimum counts. Supports AND logic — all specified tags must be present
with at least the minimum count. Case-insensitive matching.

---

## Trigger

```
API Gateway: POST /query/tags
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
  "tags": {
    "felis_catus": 1,
    "Sus_scrofa": 2
  }
}
```

> Tag names are case-insensitive — `felis_catus`, `Felis_catus`, `FELIS_CATUS` all work.

---

## Response

```json
{
  "results": [
    {
      "mediaId": "uuid-here",
      "originalName": "Felis_catus_1.JPG",
      "contentType": "image/jpeg",
      "fileKind": "image",
      "tags": { "Felis_catus": 1 },
      "fullUrl": "https://presigned-s3-url...",
      "thumbnailUrl": "https://presigned-s3-url...",
      "status": "ready",
      "createdAt": "2026-06-05T12:12:32",
      "size": 2393484
    }
  ],
  "count": 1
}
```

---

## Flow

```
Frontend → POST /query/tags {tags: {species: min_count}}
  → Normalize search tags to lowercase
  → Scan DynamoDB table (with pagination)
  → For each item: normalize item tags to lowercase
  → Check all requested tags present with min count (AND logic)
  → Generate presigned URLs for file and thumbnail
  → Return matching results
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
cd ecolens/backend/aws/lambda/ecolens-query

Compress-Archive -Path lambda_function.py -DestinationPath function.zip -Force

# First deploy
aws lambda create-function `
  --function-name ecolens-query `
  --runtime python3.12 `
  --role arn:aws:iam::686112929724:role/ecolens-query-role `
  --handler lambda_function.lambda_handler `
  --zip-file fileb://function.zip `
  --timeout 30 `
  --memory-size 256 `
  --region ap-southeast-4

# Update existing
aws lambda update-function-code `
  --function-name ecolens-query `
  --zip-file fileb://function.zip `
  --region ap-southeast-4
```

---

## API Gateway Integration

```
Resource:    /query/tags
Method:      POST
Type:        AWS_PROXY
Resource ID: x0yile
API ID:      g4raf95x4b
```

---

## Verification

```powershell
$body = '{"tags": {"felis_catus": 1}}'

Invoke-RestMethod `
  -Uri "https://g4raf95x4b.execute-api.ap-southeast-4.amazonaws.com/dev/query/tags" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

Expected: Results array with matching files ✅

---

## Checklist

```
☑ Lambda created (ecolens-query)
☑ Runtime: Python 3.12
☑ Role: ecolens-query-role
☑ Timeout: 30s
☑ Memory: 256MB
☑ API Gateway POST /query/tags connected
☑ Case-insensitive tag matching
☑ Pagination handled for large datasets
☑ Presigned URLs generated for files and thumbnails
☑ Frontend search working
```
