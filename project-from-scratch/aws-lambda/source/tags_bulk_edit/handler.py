from common.core import clean_tags, current_user, find_media_by_urls, handle_options, list_owner_media, media_table, parse_body, response


def handler(event, context):
    options = handle_options(event)
    if options:
        return options
    try:
        user = current_user(event)
        body = parse_body(event)
        ids = set(body.get("ids") or [])
        urls = body.get("urls") or []
        tags = clean_tags(body.get("tags") or [])
        operation = int(body.get("operation"))
        selected = find_media_by_urls(user["id"], urls)
        selected.extend([item for item in list_owner_media(user["id"]) if item["id"] in ids])
        updated = []
        for item in {item["id"]: item for item in selected}.values():
            counts = {tag["name"]: int(tag["count"]) for tag in item.get("tags", [])}
            for tag in tags:
                if operation == 1:
                    counts[tag] = max(1, counts.get(tag, 0) + 1)
                else:
                    counts.pop(tag, None)
            media_table().update_item(
                Key={"ownerId": user["id"], "id": item["id"]},
                UpdateExpression="SET tags = :tags",
                ExpressionAttributeValues={":tags": counts},
            )
            item["tags"] = [{"name": name, "count": count} for name, count in counts.items()]
            updated.append(item)
        return response(200, updated)
    except Exception as exc:
        return response(500, {"error": str(exc)})
