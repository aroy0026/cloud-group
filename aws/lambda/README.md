## Aussie EcoLens Lambda Functions

These folders map to the frontend API routes in `frontend/src/app/api.ts`.

Recommended environment variables:

- `MEDIA_TABLE`: DynamoDB table with partition key `ownerId` and sort key `id`
- `CHECKSUM_TABLE`: DynamoDB table with partition key `checksum`
- `SUBSCRIPTIONS_TABLE`: DynamoDB table with partition key `ownerId`
- `SETTINGS_TABLE`: DynamoDB table with partition key `ownerId`
- `UPLOAD_BUCKET`: private S3 bucket for uploaded media
- `SIGNED_URL_EXPIRES`: optional, default `900`
- `GET_URL_EXPIRES`: optional browser preview/download URL expiry in seconds, default `3600`
- `CORS_ORIGIN`: optional, default `*`
- `SNS_TOPIC_PREFIX`: optional, e.g. `arn:aws:sns:ap-southeast-2:123456789012:ecolens-`
- `QUERY_FILE_PROCESSOR_URL`: optional Cloud Run endpoint for query-by-uploaded-file ML detection
- `LABELS_PATH`: optional SpeciesNet labels file path, default `common/labels.txt`

API Gateway should attach a Cognito JWT authorizer to every route except browser `OPTIONS`.
The handlers read Cognito claims from `event.requestContext.authorizer.jwt.claims`.

Route mapping:

- `POST /upload/prepare` -> `upload_prepare`
- `POST /upload/complete` -> `upload_complete`
- `POST /upload` -> `upload`
- `GET /files` -> `files_list`
- `POST /files/delete` -> `files_delete`
- `POST /query/by-tags` -> `query_by_tags`
- `POST /query/by-species` -> `query_by_species`
- `POST /query/by-thumbnail` -> `query_by_thumbnail`
- `POST /query/by-file` -> `query_by_file`
- `POST /tags/bulk-edit` -> `tags_bulk_edit`
- `GET|POST|DELETE /notifications/subscriptions` -> `notifications_subscriptions`
- `PUT /notifications/settings` -> `notifications_settings`
- S3 `ObjectCreated` trigger -> `media_processor`

`media_processor` generates real image thumbnails after S3 upload using OpenCV. It
downloads the original image, resizes it while maintaining aspect ratio, compresses
it to JPEG, stores it under `thumbnails/<ownerId>/<mediaId>/...jpg`, and saves the
thumbnail storage URL in DynamoDB. Package `opencv-python-headless` with
`ecolens-media-processor`.

For videos, `media_processor` follows the assignment requirement by extracting one
JPEG frame per second with OpenCV, storing those frames under
`frames/<ownerId>/<mediaId>/frame_000001.jpg`, and generating the video thumbnail
from the first extracted frame. The DynamoDB record stores `framePrefix`,
`frameS3Uris`, and `frameCount` so a GCP Cloud Run ML service can run inference
over the extracted S3 frames.

The signed upload flow does not trust browser-provided checksums. `/upload/prepare`
only creates a pending upload reservation and a pre-signed S3 URL. After the file
is uploaded, `/upload/complete` reads the S3 object, computes the SHA-256 checksum
inside Lambda, checks the checksum table for duplicates, and only then writes the
final media record.

Media records keep stable `s3://...` storage pointers in DynamoDB. API responses
convert those pointers into pre-signed HTTPS `fullUrl`, `thumbnail`, and
`thumbnailUrl` values so the React UI can preview images and open full media
without making the S3 bucket public.

The shared helper parses the Aussie EcoLens `labels.txt` format:

```text
uuid;class;order;family;genus;species;common name
```

Tags are stored as normalized common names such as `dingo`, `australian_magpie`,
`common_wombat`, and `eastern_gray_kangaroo`. Scientific aliases such as
`canis_dingo` and useful common-name words such as `kangaroo` are accepted for
filename inference and query matching support.
