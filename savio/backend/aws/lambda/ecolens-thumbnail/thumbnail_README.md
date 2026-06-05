# ecolens-thumbnail
## EcoLens Lambda Function

---

## What This Does

Automatically generates a 300x300 JPEG thumbnail whenever an image is
uploaded to the S3 `uploads/` folder. Triggered by S3 event — no API
Gateway involvement. Updates the DynamoDB record with the thumbnail URL.

---

## Trigger

```
S3 Event: s3:ObjectCreated:* on prefix uploads/
Bucket:   ecolens-media-savio-melbourne
```

---

## IAM Role

```
ecolens-thumbnail-role
```

---

## Flow

```
S3 upload to uploads/ → S3 fires event → Lambda triggered
  → Download original image from S3
  → Convert to RGB (handles PNG transparency)
  → Resize to 300x300 using Pillow (LANCZOS)
  → Save as JPEG quality 85
  → Upload to thumbnails/ folder in S3
  → Find DynamoDB record by s3_key
  → Update thumbnail_url field
```

---

## Key Config

```python
BUCKET_NAME    = 'ecolens-media-savio-melbourne'
TABLE_NAME     = 'ecolens-media'
THUMBNAIL_SIZE = (300, 300)
REGION         = 'ap-southeast-4'
```

---

## Dependencies

Pillow is bundled into the deployment package (not a Lambda layer):

```powershell
pip install pillow `
  --target ./package `
  --platform manylinux2014_x86_64 `
  --only-binary=:all: `
  --python-version 3.12

Copy-Item lambda_function.py package/
Compress-Archive -Path package/* -DestinationPath function.zip -Force
```

---

## Deploy / Update

```powershell
cd ecolens/backend/aws/lambda/ecolens-thumbnail

# First deploy
aws lambda create-function `
  --function-name ecolens-thumbnail `
  --runtime python3.12 `
  --role arn:aws:iam::686112929724:role/ecolens-thumbnail-role `
  --handler lambda_function.lambda_handler `
  --zip-file fileb://function.zip `
  --timeout 60 `
  --memory-size 512 `
  --region ap-southeast-4

# Update existing
aws lambda update-function-code `
  --function-name ecolens-thumbnail `
  --zip-file fileb://function.zip `
  --region ap-southeast-4
```

---

## S3 Trigger Setup

```powershell
# Grant S3 permission to invoke Lambda
aws lambda add-permission `
  --function-name ecolens-thumbnail `
  --statement-id s3-trigger `
  --action lambda:InvokeFunction `
  --principal s3.amazonaws.com `
  --source-arn arn:aws:s3:::ecolens-media-savio-melbourne `
  --region ap-southeast-4

# Add S3 event notification
aws s3api put-bucket-notification-configuration `
  --bucket ecolens-media-savio-melbourne `
  --notification-configuration file://s3-trigger.json
```

`s3-trigger.json`:
```json
{
  "LambdaFunctionConfigurations": [{
    "LambdaFunctionArn": "arn:aws:lambda:ap-southeast-4:686112929724:function:ecolens-thumbnail",
    "Events": ["s3:ObjectCreated:*"],
    "Filter": {
      "Key": {
        "FilterRules": [{"Name": "prefix", "Value": "uploads/"}]
      }
    }
  }]
}
```

---

## Verification

1. Upload an image via the frontend
2. Check **S3 → thumbnails/** — thumbnail file should appear
3. Check **DynamoDB → ecolens-media** — `thumbnail_url` field populated

---

## Checklist

```
☑ Lambda created (ecolens-thumbnail)
☑ Runtime: Python 3.12
☑ Role: ecolens-thumbnail-role
☑ Timeout: 60s
☑ Memory: 512MB
☑ Pillow bundled in deployment package
☑ S3 permission granted for Lambda invocation
☑ S3 event trigger configured on uploads/ prefix
☑ Thumbnail generation working
☑ DynamoDB thumbnail_url updated correctly
```
