from common.core import current_user, handle_options, list_owner_media, parse_body, response


def handler(event, context):
    options = handle_options(event)
    if options:
        return options
    try:
        user = current_user(event)
        body = parse_body(event)
        conditions = body.get("conditions") or []
        cleaned = [(c.get("tag", "").strip().lower(), int(c.get("minCount") or 1)) for c in conditions]
        results = []
        for item in list_owner_media(user["id"]):
            tags = {tag["name"].lower(): int(tag["count"]) for tag in item.get("tags", [])}
            if all(tag and tags.get(tag, 0) >= min_count for tag, min_count in cleaned):
                results.append(item)
        return response(200, results)
    except Exception as exc:
        return response(500, {"error": str(exc)})
