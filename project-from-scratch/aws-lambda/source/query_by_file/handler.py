from common.core import (
    current_user,
    detect_tags_with_processor,
    handle_options,
    header_value,
    infer_tags_from_name,
    list_owner_media,
    raw_body_bytes,
    response,
)


def handler(event, context):
    options = handle_options(event)
    if options:
        return options
    try:
        user = current_user(event)
        tags = detect_query_tags(event)
        names = set(tags.keys())
        results = []
        for item in list_owner_media(user["id"]):
            item_tags = {tag["name"] for tag in item.get("tags", [])}
            if names and names.issubset(item_tags):
                results.append(item)
        return response(200, results)
    except Exception as exc:
        return response(500, {"error": str(exc)})


def detect_query_tags(event):
    payload = raw_body_bytes(event)
    if payload:
        tags = detect_tags_with_processor(payload, header_value(event, "content-type", "application/octet-stream"))
        if tags:
            return tags
    query = event.get("queryStringParameters") or {}
    return infer_tags_from_name(query.get("name") or "query_file")
