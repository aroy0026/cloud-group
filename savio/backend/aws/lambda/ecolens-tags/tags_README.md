# ecolens-tags
## EcoLens Lambda Function

---

## What This Does

Handles bulk tag add/remove operations on multiple files at once.
Finds DynamoDB records by file URL and updates the tags field.
Supports both adding new tags and removing existing ones.

---

## Trigger

```
API Gateway: POST /tags
```

---

## IAM Role

```
ecolens-tags-role
```

---

## Request Body

```json
{
  "urls": [
    "https://ecolens-media-savio-melbourne.s3.ap-southeast-4.amazonaws.com/uploads/images/uuid_file.JPG"
  ],
  "tags": ["koala", "tree"],
  "operation": 1
}
```

| Field | Values | Description |
|---|---|---|
| `urls` | Array of S3 URLs | Files to update |
| `tags` | Array of tag strings | Tags to add or remove |
| `operation` | `1` = add, `0` = remove | Which operation to perform |

---

## Response

```json
{
  "message": "Added tags for 1 file(s)",
  "updated": 1,
  "failed": []
}
```

---

## Flow

```
Frontend → POST /tags {urls, tags, operation}
  → For each URL:
      → Strip query params (handles presigned URLs)
      → Scan DynamoDB for matching file_url or thumbnail_url
      → If operation=1: increment tag count (or set to 1 if new)
      → If operation=0: remove tag from map
      → Update DynamoDB tags field
  → Return updated count + failed list
```

---

## Key Config

```python
TABLE_NAME  = 'ecolens-media'
REGION      = 'ap-southeast-4'
```

---

## Deploy / Update

```powershell
cd ecolens/backend/aws/lambda/ecolens-tags

Compress-Archive -Path lambda_function.py -DestinationPath function.zip -Force

# First deploy
aws lambda create-function `
  --function-name ecolens-tags `
  --runtime python3.12 `
  --role arn:aws:iam::686112929724:role/ecolens-tags-role `
  --handler lambda_function.lambda_handler `
  --zip-file fileb://function.zip `
  --timeout 30 `
  --memory-size 256 `
  --region ap-southeast-4

# Update existing
aws lambda update-function-code `
  --function-name ecolens-tags `
  --zip-file fileb://function.zip `
  --region ap-southeast-4
```

---

## API Gateway Integration

```
Resource:    /tags
Method:      POST
Type:        AWS_PROXY
Resource ID: onlhs0
API ID:      g4raf95x4b
```

---

## Known UI Issue

The TagsPage requires file URLs to be pasted manually. A future improvement
would allow selecting files from the media library directly.

---

## Checklist

```
☑ Lambda created (ecolens-tags)
☑ Runtime: Python 3.12
☑ Role: ecolens-tags-role
☑ Timeout: 30s
☑ Memory: 256MB
☑ API Gateway POST /tags connected
☑ Add tags working (operation=1)
☑ Remove tags working (operation=0)
☑ Presigned URL normalization (strips query params)
☑ Bulk operations across multiple files
```
