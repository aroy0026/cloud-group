# Firestore Schema

## media/{mediaId}

```json
{
  "mediaId": "uuid",
  "ownerId": "cognito-sub",
  "ownerEmail": "user@example.com",
  "originalName": "Felis_catus_1.JPG",
  "contentType": "image/jpeg",
  "fileKind": "image",
  "sha256": "hex",
  "status": "PRESIGNED|QUEUED|PROCESSING|READY|FAILED|DUPLICATE_REMOVED",
  "s3Url": "s3://bucket/key",
  "gcsUri": "gs://bucket/originals/...",
  "thumbnailUrl": "gs://bucket/thumbnails/...",
  "fullUrl": "gs://bucket/classified/felis_catus/...",
  "primaryTag": "felis_catus",
  "sortedUrls": {"felis_catus": "gs://bucket/classified/felis_catus/..."},
  "sortedUrlList": ["gs://bucket/classified/felis_catus/..."],
  "tags": {"felis_catus": 1},
  "tagList": ["felis_catus"],
  "createdAt": "server timestamp",
  "updatedAt": "server timestamp",
  "error": "optional"
}
```

## checksums/{sha256}

```json
{
  "mediaId": "uuid",
  "ownerId": "cognito-sub",
  "firstSeenAt": "server timestamp"
}
```

## thumbnailIndex/{safeThumbnailId}

```json
{
  "mediaId": "uuid",
  "thumbnailUrl": "gs://bucket/thumbnails/...",
  "fullImageUrl": "gs://bucket/originals/..."
}
```

## userWatches/{userId_tag}

```json
{
  "userId": "cognito-sub",
  "email": "user@example.com",
  "tag": "dingo",
  "snsTopicArn": "arn:aws:sns:...",
  "active": true
}
```
