# API Contract

All routes except Cognito Hosted UI require an `Authorization: Bearer <Cognito ID token>` header.

## POST /uploads/presign

Request:

```json
{
  "filename": "Felis_catus_1.JPG",
  "contentType": "image/jpeg",
  "size": 123456,
  "sha256": "hex"
}
```

Response:

```json
{
  "duplicate": false,
  "mediaId": "uuid",
  "objectKey": "uploads/user/media.jpg",
  "uploadUrl": "https://..."
}
```

Duplicate response:

```json
{
  "duplicate": true,
  "existingMediaId": "uuid"
}
```

## POST /query/tags

Request:

```json
{"tags": {"felis_catus": 1, "canis_familiaris": 1}}
```

Returns only records where all requested tags meet minimum counts.

## POST /query/species

Request:

```json
{"species": "dingo"}
```

## POST /query/thumbnail

Request:

```json
{"thumbnailUrl": "gs://bucket/thumbnails/user/media.jpg"}
```

## POST /query/file

Body is raw image bytes. The query file is processed temporarily and must not create a permanent media record.

## POST /media/tags/bulk

Request:

```json
{
  "urls": ["gs://bucket/originals/user/media.jpg"],
  "tags": ["reviewed"],
  "operation": 1
}
```

`operation = 1` adds tags. `operation = 0` removes tags.

## POST /media/delete

Request:

```json
{"urls": ["gs://bucket/originals/user/media.jpg"]}
```

Deletes original, thumbnail, checksum index, thumbnail index, and media document.

