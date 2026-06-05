from botocore.exceptions import ClientError

from common.core import (
    BadRequest,
    checksum_table,
    current_user,
    delete_media,
    get_media,
    handle_options,
    media_table,
    now_iso,
    parse_body,
    put_media,
    response,
    s3,
    s3_sha256,
    s3_url,
)


def handler(event, context):
    options = handle_options(event)
    if options:
        return options
    try:
        user = current_user(event)
        body = parse_body(event)
        media_id = body.get("fileId")
        if not media_id:
            raise BadRequest("fileId is required")

        reservation = media_table().get_item(Key={"ownerId": user["id"], "id": media_id}).get("Item")
        if not reservation:
            raise BadRequest("Upload reservation not found")

        bucket = reservation["bucket"]
        key = reservation["key"]
        checksum = s3_sha256(bucket, key)
        existing = checksum_table().get_item(Key={"checksum": checksum}).get("Item")
        if existing and existing.get("mediaId") != media_id:
            existing_media = get_media(existing.get("ownerId", user["id"]), existing["mediaId"])
            s3.delete_object(Bucket=bucket, Key=key)
            delete_media(user["id"], media_id)
            return response(200, {"duplicate": True, "file": existing_media})

        item = {
            "ownerId": user["id"],
            "id": media_id,
            "name": body.get("name") or reservation.get("name"),
            "type": "video" if (body.get("mimeType") or reservation.get("mimeType") or "").startswith("video") else "image",
            "mimeType": body.get("mimeType") or reservation.get("mimeType"),
            "size": int(body.get("size") or reservation.get("size") or 0),
            "checksum": checksum,
            "bucket": bucket,
            "key": key,
            "fullUrl": s3_url(bucket, key),
            "thumbnail": reservation.get("thumbnail") or "",
            "tags": reservation.get("tags") or {},
            "status": reservation.get("status") if reservation.get("status") == "READY" else "UPLOADED",
            "createdAt": reservation.get("createdAt") or now_iso(),
            "updatedAt": now_iso(),
        }
        if not existing:
            checksum_table().put_item(
                Item={"checksum": checksum, "ownerId": user["id"], "mediaId": media_id, "status": "ACTIVE"},
                ConditionExpression="attribute_not_exists(checksum)",
            )
        return response(200, put_media(item))
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            return response(409, {"error": "A matching checksum was written by another request. Try refreshing the media list."})
        return response(500, {"error": str(exc)})
    except Exception as exc:
        return response(400 if isinstance(exc, BadRequest) else 500, {"error": str(exc)})
