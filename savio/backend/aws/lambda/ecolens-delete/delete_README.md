# ecolens-delete
## EcoLens Lambda Function

---

## What This Does

Deletes files completely from both S3 and DynamoDB. For each URL provided,
finds the DynamoDB record, deletes the original file and thumbnail from S3,
then removes the DynamoDB record.

---

## Trigger

```
API Gateway: POST /delete
```

---

## IAM Role

```
ecolens-delete-role
```

---

## Request Body

```json
{
  "urls": [
    "https://ecolens-media-savio-melbourne.s3.ap-southeast-4.amazonaws.com/uploads/images/uuid_file.JPG"
  ]
}
```

---

## Response

```json
{
  "message": "Deleted 1 file(s)",
  "deleted": 1,
  "failed": []
}
```

---

## Flow

```
Frontend → POST /delete {urls}
  → For each URL:
      → Strip query params (handles presigned URLs)
      → Scan DynamoDB for matching file_url
      → Delete original file from S3 uploads/
      → Delete thumbnail from S3 thumbnails/
      → Delete DynamoDB record
  → Return deleted count + failed list
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
cd ecolens/backend/aws/lambda/ecolens-delete

Compress-Archive -Path lambda_function.py -DestinationPath function.zip -Force

# First deploy
aws lambda create-function `
  --function-name ecolens-delete `
  --runtime python3.12 `
  --role arn:aws:iam::686112929724:role/ecolens-delete-role `
  --handler lambda_function.lambda_handler `
  --zip-file fileb://function.zip `
  --timeout 30 `
  --memory-size 256 `
  --region ap-southeast-4

# Update existing
aws lambda update-function-code `
  --function-name ecolens-delete `
  --zip-file fileb://function.zip `
  --region ap-southeast-4
```

---

## API Gateway Integration

```
Resource:    /delete
Method:      POST
Type:        AWS_PROXY
Resource ID: 745qcn
API ID:      g4raf95x4b
```

---

## Verification

```powershell
$body = '{"urls": ["https://ecolens-media-savio-melbourne.s3.ap-southeast-4.amazonaws.com/uploads/images/uuid_file.JPG"]}'

Invoke-RestMethod `
  -Uri "https://g4raf95x4b.execute-api.ap-southeast-4.amazonaws.com/dev/delete" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

Expected: `deleted: 1`, file gone from S3 and DynamoDB ✅

---

## Checklist

```
☑ Lambda created (ecolens-delete)
☑ Runtime: Python 3.12
☑ Role: ecolens-delete-role
☑ Timeout: 30s
☑ Memory: 256MB
☑ API Gateway POST /delete connected
☑ Deletes original file from S3 uploads/
☑ Deletes thumbnail from S3 thumbnails/
☑ Deletes DynamoDB record
☑ Presigned URL normalization
☑ Bulk delete across multiple files
```
