# AWS Lambda Setup

This folder contains all Lambda source needed by the AWS backend.

Source code lives in:

```text
source/
  common/
  upload_prepare/
  upload_complete/
  files_list/
  files_delete/
  media_processor/
  query_by_tags/
  query_by_species/
  query_by_thumbnail/
  query_by_file/
  tags_bulk_edit/
  notifications_subscriptions/
  notifications_settings/
```

## What Each Function Does

| Function | Route/Event | Purpose |
| --- | --- | --- |
| `ecolens-upload-prepare` | `POST /upload/prepare` | Create media reservation and pre-signed S3 PUT URL. |
| `ecolens-upload-complete` | `POST /upload/complete` | Compute Lambda-side checksum and finalize upload or detect duplicate. |
| `ecolens-files-list` | `GET /files` | Return user media records with pre-signed browser URLs. |
| `ecolens-files-delete` | `POST /files/delete` | Delete original, thumbnail, frames, checksum, and DynamoDB record. |
| `ecolens-media-processor` | S3 ObjectCreated | Generate thumbnails, extract video frames, call GCP Cloud Run ML, save tags. |
| `ecolens-query-by-tags` | `POST /query/by-tags` | Logical AND tag/count query. |
| `ecolens-query-by-species` | `POST /query/by-species` | Species query. |
| `ecolens-query-by-thumbnail` | `POST /query/by-thumbnail` | Resolve thumbnail URL to matching media. |
| `ecolens-query-by-file` | `POST /query/by-file` | Temporary file ML query, then find matching media. |
| `ecolens-tags-bulk-edit` | `POST /tags/bulk-edit` | Bulk add/remove tags. |
| `ecolens-notifications-subscriptions` | `GET/POST/DELETE /notifications/subscriptions` | Watch/unwatch tags and create SNS email subscriptions. |
| `ecolens-notifications-settings` | `PUT /notifications/settings` | Save per-user notification preferences. |

## Required Environment Variables

```text
MEDIA_TABLE=ecolens-media
CHECKSUM_TABLE=ecolens-checksums
SUBSCRIPTIONS_TABLE=ecolens-subscriptions
SETTINGS_TABLE=ecolens-settings
UPLOAD_BUCKET=ecolens-upload-bucket
SIGNED_URL_EXPIRES=900
GET_URL_EXPIRES=3600
CORS_ORIGIN=http://localhost:5173
SNS_TOPIC_PREFIX=ecolens-
QUERY_FILE_PROCESSOR_URL=<cloud-run-url>/query-file
QUERY_FILE_PROCESSOR_TIMEOUT=120
CLOUD_RUN_AUDIENCE=<cloud-run-url>
GCP_WIF_CREDENTIAL_CONFIG_SECRET=ecolens-gcp-wif-credential-config
GCP_SERVICE_ACCOUNT_EMAIL=<gcp-service-account-email>
VIDEO_MAX_FRAMES=12
THUMBNAIL_MAX_DIMENSION=480
THUMBNAIL_QUALITY=78
VIDEO_FRAME_JPEG_QUALITY=82
```

## Package Lambdas

Run from this folder:

```bash
set -a
source ../.env
set +a
./package-lambdas.sh
```

Output zips go to:

```text
dist/
```

Notes:

- `media_processor` includes `opencv-python-headless`, `google-auth`, and `requests`.
- `query_by_file` includes `google-auth` and `requests`.
- Other functions use the AWS Lambda built-in `boto3` runtime library.

## Deploy Lambdas

Prerequisites:

- S3 upload bucket exists.
- DynamoDB tables exist.
- Lambda execution role exists.
- Cloud Run URL and WIF env vars are filled in `.env`.

Run:

```bash
./deploy-lambdas.sh
```

## S3 Trigger

After `ecolens-media-processor` exists, configure the upload bucket trigger:

```bash
./configure-s3-trigger.sh
```

The trigger listens to:

```text
s3:ObjectCreated:*
prefix uploads/
```

The media processor ignores `thumbnails/` and `frames/` objects to avoid loops.

## Video Processing

For videos:

1. Extract roughly one frame per second.
2. Cap extracted frames using `VIDEO_MAX_FRAMES`, currently `12`.
3. Use the first extracted frame as the thumbnail.
4. Save thumbnail and DynamoDB preview before ML tagging.
5. Send frames to GCP Cloud Run for ML.
6. Store the highest count per species across frames, not the sum.

