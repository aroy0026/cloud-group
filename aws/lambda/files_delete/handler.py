from common.core import checksum_table, current_user, delete_media, find_media_by_urls, handle_options, parse_s3_url, parse_body, response, s3


def handler(event, context):
    options = handle_options(event)
    if options:
        return options
    try:
        user = current_user(event)
        body = parse_body(event)
        ids = set(body.get("ids") or [])
        urls = body.get("urls") or []
        selected = find_media_by_urls(user["id"], urls)
        selected.extend([item for item in __import__("common.core", fromlist=["list_owner_media"]).list_owner_media(user["id"]) if item["id"] in ids])
        deleted = []
        for item in {item["id"]: item for item in selected}.values():
            bucket, key = parse_s3_url(item.get("fullUrl"))
            if bucket and key:
                s3.delete_object(Bucket=bucket, Key=key)
            thumb_bucket, thumb_key = parse_s3_url(item.get("thumbnail"))
            if thumb_bucket and thumb_key:
                s3.delete_object(Bucket=thumb_bucket, Key=thumb_key)
            for frame_uri in item.get("frameS3Uris") or []:
                frame_bucket, frame_key = parse_s3_url(frame_uri)
                if frame_bucket and frame_key:
                    s3.delete_object(Bucket=frame_bucket, Key=frame_key)
            delete_prefix(item.get("framePrefix"))
            if item.get("checksum"):
                checksum_table().delete_item(Key={"checksum": item["checksum"]})
            delete_media(user["id"], item["id"])
            deleted.append(item["id"])
        return response(200, {"deletedIds": deleted})
    except Exception as exc:
        return response(500, {"error": str(exc)})


def delete_prefix(uri):
    bucket, prefix = parse_s3_url(uri)
    if not bucket or not prefix:
        return
    if not prefix.endswith("/"):
        prefix = f"{prefix}/"
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        objects = [{"Key": item["Key"]} for item in page.get("Contents", [])]
        if objects:
            s3.delete_objects(Bucket=bucket, Delete={"Objects": objects})
