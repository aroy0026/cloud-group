from common.core import current_user, handle_options, list_owner_media, parse_body, parse_s3_url, response


def handler(event, context):
    options = handle_options(event)
    if options:
        return options
    try:
        user = current_user(event)
        thumbnail_url = (parse_body(event).get("thumbnailUrl") or "").strip()
        thumbnail_location = parse_s3_url(thumbnail_url)
        has_thumbnail_location = all(thumbnail_location)
        results = [
            item
            for item in list_owner_media(user["id"])
            if item.get("thumbnail") == thumbnail_url
            or item.get("thumbnailUrl") == thumbnail_url
            or (has_thumbnail_location and parse_s3_url(item.get("thumbnail")) == thumbnail_location)
            or (has_thumbnail_location and parse_s3_url(item.get("thumbnailUrl")) == thumbnail_location)
            or (has_thumbnail_location and parse_s3_url(item.get("thumbnailS3Uri")) == thumbnail_location)
        ]
        return response(200, results)
    except Exception as exc:
        return response(500, {"error": str(exc)})
