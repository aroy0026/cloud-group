# S3 Upload Bucket Setup

S3 stores:

- Original uploads under `uploads/`
- Image thumbnails under `thumbnails/`
- Extracted video frames under `frames/`
- Lambda deployment artifacts under `lambda-artifacts/`

The bucket must stay private. Browser upload and preview access use pre-signed URLs.

## Create Bucket

```bash
set -a
source ../.env
set +a
./create-bucket.sh
```

## CORS

The script applies CORS for the frontend origin:

```text
http://localhost:5173
```

For production hosting, add your deployed frontend URL.

## Event Trigger

The S3 trigger is configured after Lambda deployment from:

```text
../aws-lambda/configure-s3-trigger.sh
```

It listens only to:

```text
uploads/
```

