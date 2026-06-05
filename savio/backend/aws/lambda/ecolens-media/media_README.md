# ecolens-media
## EcoLens Lambda Function

---

## What This Does

Returns all media items from DynamoDB sorted by upload date (newest first).
Used by the dashboard and upload page to populate the media library.
Generates presigned URLs for all file and thumbnail URLs.

---

## Trigger

```
API Gateway: GET /media
```

---

## IAM Role

```
ecolens-media-role
```

---

## Response

```json
{
  "results": [
    {
      "mediaId": "uuid-here",
      "originalName": "Canis_familiaris_1.JPG",
      "contentType": "image/jpeg",
      "fileKind": "image",
      "tags": { "Canis_familiaris": 1 },
      "fullUrl": "https://presigned-url...",
      "thumbnailUrl": "https://presigned-url...",
      "status": "ready",
      "createdAt": "2026-06-05T12:12:32",
      "size": 776032
    }
  ],
  "count": 1
}
```

---

## Flow

```
Frontend → GET /media
  → Scan entire DynamoDB table (with pagination)
  → Sort by uploaded_at descending
  → Generate presigned URLs for each file and thumbnail
  → Return normalized results
```

---

## Key Config

```python
BUCKET_NAME = 'ecolens-media-savio-melbourne'
TABLE_NAME  = 'ecolens-media'
REGION      = 'ap-southeast-4'
```

---

## IAM Role Setup

```powershell
[System.IO.File]::WriteAllText("$env:TEMP\trust-policy.json", '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}')

aws iam create-role `
  --role-name ecolens-media-role `
  --assume-role-policy-document file://$env:TEMP/trust-policy.json

[System.IO.File]::WriteAllText("$env:TEMP\media-policy.json", '{"Version":"2012-10-17","Statement":[{"Sid":"DynamoDBReadAccess","Effect":"Allow","Action":["dynamodb:Scan"],"Resource":"arn:aws:dynamodb:ap-southeast-4:686112929724:table/ecolens-media"},{"Sid":"S3ReadAccess","Effect":"Allow","Action":["s3:GetObject"],"Resource":"arn:aws:s3:::ecolens-media-savio-melbourne/*"},{"Sid":"CloudWatchLogsAccess","Effect":"Allow","Action":["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],"Resource":"arn:aws:logs:ap-southeast-4:686112929724:log-group:/aws/lambda/ecolens-media:*"}]}')

aws iam put-role-policy `
  --role-name ecolens-media-role `
  --policy-name ecolens-media-policy `
  --policy-document file://$env:TEMP/media-policy.json
```

---

## Deploy / Update

```powershell
cd ecolens/backend/aws/lambda/ecolens-media

Compress-Archive -Path lambda_function.py -DestinationPath function.zip -Force

# First deploy (wait 10s after role creation)
aws lambda create-function `
  --function-name ecolens-media `
  --runtime python3.12 `
  --role arn:aws:iam::686112929724:role/ecolens-media-role `
  --handler lambda_function.lambda_handler `
  --zip-file fileb://function.zip `
  --timeout 30 `
  --memory-size 256 `
  --region ap-southeast-4

# Update existing
aws lambda update-function-code `
  --function-name ecolens-media `
  --zip-file fileb://function.zip `
  --region ap-southeast-4
```

---

## API Gateway Integration

```
Resource:    /media
Method:      GET
Type:        AWS_PROXY
Resource ID: or0hwx
API ID:      g4raf95x4b
```

---

## Verification

```powershell
Invoke-RestMethod `
  -Uri "https://g4raf95x4b.execute-api.ap-southeast-4.amazonaws.com/dev/media" `
  -Method GET
```

Expected: Array of media items with presigned URLs ✅

---

## Checklist

```
☑ ecolens-media-role created with minimal permissions
☑ Lambda created (ecolens-media)
☑ Runtime: Python 3.12
☑ Role: ecolens-media-role
☑ Timeout: 30s
☑ Memory: 256MB
☑ API Gateway GET /media connected
☑ Pagination handled
☑ Sorted by newest first
☑ Presigned URLs generated
☑ Dashboard populating correctly
```
