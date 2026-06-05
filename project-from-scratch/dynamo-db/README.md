# DynamoDB Tables

This folder documents the DynamoDB side of the deployed Aussie EcoLens AWS backend.

## Tables

| Env var | Table | Keys | Purpose |
| --- | --- | --- | --- |
| `MEDIA_TABLE` | `ecolens-media` | partition `ownerId`, sort `id` | Media metadata, status, tags, S3 URLs, thumbnails, video frame metadata. |
| `CHECKSUM_TABLE` | `ecolens-checksums` | partition `checksum` | Duplicate detection after Lambda computes SHA-256 from S3 object bytes. |
| `SUBSCRIPTIONS_TABLE` | `ecolens-subscriptions` | partition `ownerId` | Per-user watched tag subscriptions. |
| `SETTINGS_TABLE` | `ecolens-settings` | partition `ownerId` | Per-user notification settings. |

All tables use on-demand billing (`PAY_PER_REQUEST`) for coursework simplicity.

## Used By

The Lambda handlers in `../aws/lambda/` read these table names through environment variables:

```text
MEDIA_TABLE=ecolens-media
CHECKSUM_TABLE=ecolens-checksums
SUBSCRIPTIONS_TABLE=ecolens-subscriptions
SETTINGS_TABLE=ecolens-settings
```

## Create Tables

Run:

```bash
./create-tables.sh
```

The script is idempotent enough for setup work: it skips a table if AWS says it already exists.

## Media Record Shape

Video records include:

```json
{
  "ownerId": "cognito-sub",
  "id": "media-id",
  "type": "video",
  "fullUrl": "s3://bucket/uploads/...",
  "thumbnail": "s3://bucket/thumbnails/...",
  "framePrefix": "s3://bucket/frames/owner/media-id",
  "frameS3Uris": ["s3://bucket/frames/owner/media-id/frame_000001.jpg"],
  "frameCount": 12,
  "tags": {"canis_dingo": 1},
  "status": "READY"
}
```

The API converts `s3://` values into pre-signed browser URLs before returning data to React.

