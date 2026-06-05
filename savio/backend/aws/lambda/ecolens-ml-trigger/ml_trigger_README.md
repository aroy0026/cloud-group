# ecolens-ml-trigger
## EcoLens Lambda Function

---

## What This Does

Background ML processing Lambda. Invoked asynchronously by
`ecolens-upload-confirm` — runs without API Gateway involvement so
there is no timeout constraint. Handles both image and video ML
tagging, video thumbnail extraction, DynamoDB updates, and SNS
notifications.

---

## Trigger

```
Invoked async by: ecolens-upload-confirm Lambda
InvocationType:   Event (fire and forget — no response waited)
```

---

## IAM Role

```
ecolens-ml-trigger-role
```

---

## Input Event

```json
{
  "file_id": "uuid-here",
  "s3_key": "uploads/images/uuid_filename.jpg",
  "file_url": "https://ecolens-media-savio-melbourne.s3.ap-southeast-4.amazonaws.com/..."
}
```

---

## Flow

```
Receives event from confirm Lambda
  → Calls GCP Cloud Run /tag {file_id, s3_key}
      → If image: MegaDetector + SpeciesNet → tags
      → If video: extract 1 frame/sec → ML each frame → MAX tags + thumbnail_base64
  → If thumbnail_base64 in response:
      → Decode base64 → upload to S3 thumbnails/
      → Save thumbnail_url to DynamoDB
  → Update DynamoDB: tags + status=ready
  → Send SNS notifications for detected species
```

---

## Key Config

```python
TABLE_NAME  = 'ecolens-media'
BUCKET_NAME = 'ecolens-media-savio-melbourne'
GCP_ML_URL  = 'https://ecolens-ml-service-810236742778.australia-southeast2.run.app/tag'
REGION      = 'ap-southeast-4'
```

---

## Why a Separate Lambda?

API Gateway has a hard 29 second timeout. Video ML processing takes
several minutes (1 frame/sec × ML inference per frame). By invoking
this Lambda asynchronously, the confirm Lambda returns immediately to
the frontend while this Lambda runs in the background for up to 15
minutes.

---

## Deploy / Update

```powershell
cd ecolens/backend/aws/lambda/ecolens-ml-trigger

Compress-Archive -Path lambda_function.py -DestinationPath function.zip -Force

# First deploy (wait 10s after role creation)
aws lambda create-function `
  --function-name ecolens-ml-trigger `
  --runtime python3.12 `
  --role arn:aws:iam::686112929724:role/ecolens-ml-trigger-role `
  --handler lambda_function.lambda_handler `
  --zip-file fileb://function.zip `
  --timeout 900 `
  --memory-size 256 `
  --region ap-southeast-4

# Update existing
aws lambda update-function-code `
  --function-name ecolens-ml-trigger `
  --zip-file fileb://function.zip `
  --region ap-southeast-4
```

---

## IAM Role Setup

```powershell
[System.IO.File]::WriteAllText("$env:TEMP\ml-trigger-policy.json", '{"Version":"2012-10-17","Statement":[{"Sid":"S3ThumbnailAccess","Effect":"Allow","Action":["s3:PutObject"],"Resource":"arn:aws:s3:::ecolens-media-savio-melbourne/thumbnails/*"},{"Sid":"DynamoDBUpdateAccess","Effect":"Allow","Action":["dynamodb:UpdateItem"],"Resource":"arn:aws:dynamodb:ap-southeast-4:686112929724:table/ecolens-media"},{"Sid":"SNSNotifyAccess","Effect":"Allow","Action":["sns:CreateTopic","sns:Publish","sns:ListSubscriptionsByTopic"],"Resource":"arn:aws:sns:ap-southeast-4:686112929724:ecolens-tag-*"},{"Sid":"CloudWatchLogsAccess","Effect":"Allow","Action":["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],"Resource":"arn:aws:logs:ap-southeast-4:686112929724:log-group:/aws/lambda/ecolens-ml-trigger:*"}]}')

aws iam put-role-policy `
  --role-name ecolens-ml-trigger-role `
  --policy-name ecolens-ml-trigger-policy `
  --policy-document file://$env:TEMP/ml-trigger-policy.json
```

Also grant confirm Lambda permission to invoke this function:

```powershell
[System.IO.File]::WriteAllText("$env:TEMP\invoke-policy.json", '{"Version":"2012-10-17","Statement":[{"Sid":"InvokeMLTrigger","Effect":"Allow","Action":["lambda:InvokeFunction"],"Resource":"arn:aws:lambda:ap-southeast-4:686112929724:function:ecolens-ml-trigger"}]}')

aws iam put-role-policy `
  --role-name ecolens-upload-role `
  --policy-name ecolens-invoke-ml-trigger `
  --policy-document file://$env:TEMP/invoke-policy.json
```

---

## Checklist

```
☑ Lambda created (ecolens-ml-trigger)
☑ Runtime: Python 3.12
☑ Role: ecolens-ml-trigger-role
☑ Timeout: 900s (15 minutes)
☑ Memory: 256MB
☑ ecolens-upload-role granted lambda:InvokeFunction permission
☑ Image ML tagging working
☑ Video frame extraction working (1 frame/sec)
☑ Video thumbnail uploaded to S3
☑ DynamoDB updated with tags + thumbnail_url + status ready
☑ SNS notifications sent
```
