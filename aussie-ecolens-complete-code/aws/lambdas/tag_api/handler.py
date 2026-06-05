from common.auth import current_user
from common.gcp import firestore_client, server_timestamp
from common.response import json_response, parse_json_body
from common.storage import find_media_by_url


def handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return json_response(204, {})
    try:
        current_user(event)
        body = parse_json_body(event)
        urls = body.get("urls") or []
        tags = [t.lower() for t in body.get("tags") or []]
        operation = int(body.get("operation"))
        if operation not in (0, 1):
            return json_response(400, {"error": "operation must be 1 add or 0 remove"})
        updated, failed = apply_bulk_tag_edit(urls, tags, operation)
        return json_response(200, {"updated": updated, "failed": failed})
    except Exception as exc:
        return json_response(500, {"error": str(exc)})


def apply_bulk_tag_edit(urls, tags, operation):
    db = firestore_client()
    updated = 0
    failed = []
    for url in urls:
        docs = find_media_by_url(db, url)
        if not docs:
            failed.append({"url": url, "reason": "No matching media"})
            continue
        for doc in docs:
            item = doc.to_dict()
            counts = {k: int(v) for k, v in dict(item.get("tags", {})).items()}
            for tag in tags:
                if operation == 1:
                    counts[tag] = max(1, int(counts.get(tag, 0)))
                else:
                    counts.pop(tag, None)
            doc.reference.update(
                {
                    "tags": counts,
                    "tagList": sorted(counts.keys()),
                    "updatedAt": server_timestamp(),
                }
            )
            updated += 1
    return updated, failed
