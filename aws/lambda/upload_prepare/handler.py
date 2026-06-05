import os
import uuid

from botocore.exceptions import ClientError

from common.core import (
    BadRequest,
    current_user,
    handle_options,
    media_table,
    now_iso,
    response,
    s3,
)


def handler(event, context):
    options = handle_options(event)
    if options:
        return options
    try:
        user = current_user(event)
        body = __import__("common.core", fromlist=["parse_body"]).parse_body(event)
        name = body.get("name") or body.get("filename")
        mime_type = body.get("mimeType") or "application/octet-stream"
        size = int(body.get("size") or 0)
        if not name:
            raise BadRequest("name is required")

        media_id = str(uuid.uuid4())
        bucket = os.environ["UPLOAD_BUCKET"]
        key = f"uploads/{user['id']}/{media_id}/{safe_name(name)}"
        media_table().put_item(
            Item={
                "ownerId": user["id"],
                "id": media_id,
                "bucket": bucket,
                "key": key,
                "name": name,
                "mimeType": mime_type,
                "size": size,
                "status": "RESERVED",
                "createdAt": now_iso(),
                "updatedAt": now_iso(),
            },
            ConditionExpression="attribute_not_exists(ownerId) AND attribute_not_exists(id)",
        )
        upload_url = s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": key, "ContentType": mime_type},
            ExpiresIn=int(os.environ.get("SIGNED_URL_EXPIRES", "900")),
        )
        return response(200, {"duplicate": False, "fileId": media_id, "uploadUrl": upload_url})
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            return response(409, {"error": "Upload reservation already exists"})
        return response(500, {"error": str(exc)})
    except Exception as exc:
        return response(400 if isinstance(exc, BadRequest) else 500, {"error": str(exc)})


def safe_name(name):
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name)
