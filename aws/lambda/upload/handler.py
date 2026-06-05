import hashlib
import os
import uuid

from common.core import current_user, handle_options, now_iso, parse_body, put_media, raw_body_bytes, response, s3, s3_url


def handler(event, context):
    options = handle_options(event)
    if options:
        return options
    try:
        user = current_user(event)
        query = event.get("queryStringParameters") or {}
        body = parse_body(event) if (event.get("headers") or {}).get("content-type", "").startswith("application/json") else {}
        payload = body.get("data")
        raw = payload.encode("utf-8") if payload else raw_body_bytes(event)
        checksum = hashlib.sha256(raw).hexdigest()
        media_id = str(uuid.uuid4())
        name = body.get("name") or query.get("name") or f"{media_id}.bin"
        mime_type = body.get("mimeType") or query.get("mimeType") or "application/octet-stream"
        bucket = os.environ["UPLOAD_BUCKET"]
        key = f"uploads/{user['id']}/{media_id}/{name}"
        s3.put_object(Bucket=bucket, Key=key, Body=raw, ContentType=mime_type)
        item = {
            "ownerId": user["id"],
            "id": media_id,
            "name": name,
            "type": "video" if mime_type.startswith("video") else "image",
            "mimeType": mime_type,
            "size": len(raw),
            "checksum": checksum,
            "bucket": bucket,
            "key": key,
            "fullUrl": s3_url(bucket, key),
            "thumbnail": "",
            "tags": {},
            "status": "UPLOADED",
            "createdAt": now_iso(),
            "updatedAt": now_iso(),
        }
        return response(200, put_media(item))
    except Exception as exc:
        return response(500, {"error": str(exc)})
