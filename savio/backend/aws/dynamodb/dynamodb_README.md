# AWS DynamoDB Setup
## EcoLens — Day 1, Phase 4

---

## DynamoDB Config Reference

```
Table Name:      ecolens-media
Partition Key:   file_id (String)
Billing Mode:    PAY_PER_REQUEST
Region:          ap-southeast-4
Table ARN:       arn:aws:dynamodb:ap-southeast-4:686112929724:table/ecolens-media

GSI Name:        checksum-index
GSI Key:         checksum (String)
GSI ARN:         arn:aws:dynamodb:ap-southeast-4:686112929724:table/ecolens-media/index/checksum-index
```

---

## What This Does

DynamoDB stores metadata for every uploaded file. The `checksum-index` GSI
enables instant duplicate detection — when a file is uploaded its checksum
is queried against this index before storing, avoiding redundant uploads.

---

## Database Schema

| Field | Type | Description |
|---|---|---|
| `file_id` | String (PK) | Unique UUID for each file |
| `checksum` | String | SHA-256 hash for deduplication |
| `file_type` | String | `image` or `video` |
| `file_url` | String | Full S3 URL of original file |
| `thumbnail_url` | String | S3 URL of thumbnail image |
| `tags` | Map | Species detected e.g. `{"koala": 2}` |
| `uploaded_by` | String | Cognito user ID |
| `uploaded_at` | String | ISO timestamp |
| `status` | String | `processing` or `ready` |

---

## Step 1 — Create Table

```powershell
aws dynamodb create-table `
  --table-name ecolens-media `
  --attribute-definitions AttributeName=file_id,AttributeType=S `
  --key-schema AttributeName=file_id,KeyType=HASH `
  --billing-mode PAY_PER_REQUEST `
  --region ap-southeast-4
```

> PAY_PER_REQUEST = no provisioned capacity needed, pay only per read/write.

---

## Step 2 — Wait for Table to be ACTIVE

```powershell
aws dynamodb describe-table `
  --table-name ecolens-media `
  --region ap-southeast-4 `
  --query "Table.TableStatus"
```

Expected: `"ACTIVE"`

---

## Step 3 — Add Checksum GSI

```powershell
aws dynamodb update-table `
  --table-name ecolens-media `
  --attribute-definitions AttributeName=checksum,AttributeType=S `
  --global-secondary-index-updates '[{\"Create\":{\"IndexName\":\"checksum-index\",\"KeySchema\":[{\"AttributeName\":\"checksum\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}}]' `
  --region ap-southeast-4
```

---

## Step 4 — Wait for GSI to be ACTIVE

```powershell
aws dynamodb describe-table `
  --table-name ecolens-media `
  --region ap-southeast-4 `
  --query "Table.GlobalSecondaryIndexes[0].IndexStatus"
```

Expected: `"ACTIVE"` (can take 1-3 minutes)

---

## Verification

```powershell
aws dynamodb describe-table `
  --table-name ecolens-media `
  --region ap-southeast-4 `
  --query "Table.GlobalSecondaryIndexes[*].IndexName"
```

Expected:
```
["checksum-index"]
```

---

## Checklist

```
☑ Table created (ecolens-media) in ap-southeast-4
☑ Partition key: file_id (String)
☑ Billing mode: PAY_PER_REQUEST
☑ Table status: ACTIVE
☑ checksum-index GSI created
☑ GSI status: ACTIVE
```
