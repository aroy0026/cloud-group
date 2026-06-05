import os
import uuid

import boto3
from google.api_core.exceptions import AlreadyExists

from common.auth import current_user
from common.gcp import firestore_client, server_timestamp
from common.response import json_response, parse_json_body

s3 = boto3.client("s3")


def handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return json_response(204, {})

    try:
        user = current_user(event)
        body = parse_json_body(event)
        for key in ["filename", "contentType", "size", "sha256"]:
            if not body.get(key):
                return json_response(400, {"error": f"Missing {key}"})

        db = firestore_client()
        sha256 = body["sha256"].lower()
        checksum_ref = db.collection("checksums").document(sha256)
        media_id = str(uuid.uuid4())
        ext = extension_from_name(body["filename"])
        object_key = f"uploads/{user['id']}/{media_id}{ext}"
        bucket = os.environ["UPLOAD_BUCKET"]

        media_ref = db.collection("media").document(media_id)
        media_ref.set(
            {
                "mediaId": media_id,
                "ownerId": user["id"],
                "ownerEmail": user["email"],
                "originalName": body["filename"],
                "contentType": body["contentType"],
                "size": int(body["size"]),
                "sha256": sha256,
                "status": "PRESIGNED",
                "s3Key": object_key,
                "tags": {},
                "tagList": [],
                "createdAt": server_timestamp(),
                "updatedAt": server_timestamp(),
            }
        )

        try:
            checksum_ref.create(
                {
                    "mediaId": media_id,
                    "ownerId": user["id"],
                    "status": "RESERVED",
                    "createdAt": server_timestamp(),
                    "updatedAt": server_timestamp(),
                }
            )
        except AlreadyExists:
            media_ref.delete()
            data = checksum_ref.get().to_dict() or {}
            return json_response(
                200,
                {
                    "duplicate": True,
                    "existingMediaId": data.get("mediaId"),
                    "message": "This exact file is already uploaded or processing.",
                },
            )

        upload_url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": bucket,
                "Key": object_key,
                "ContentType": body["contentType"],
                "Metadata": {
                    "sha256": sha256,
                    "owner-id": user["id"],
                    "owner-email": user["email"],
                    "media-id": media_id,
                    "original-name": body["filename"],
                },
            },
            ExpiresIn=900,
        )

        return json_response(
            200,
            {
                "duplicate": False,
                "mediaId": media_id,
                "objectKey": object_key,
                "uploadUrl": upload_url,
            },
        )
    except Exception as exc:
        return json_response(500, {"error": str(exc)})


def extension_from_name(filename):
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[1].lower()
