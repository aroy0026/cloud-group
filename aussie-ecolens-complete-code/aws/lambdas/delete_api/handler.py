from common.auth import current_user
from common.gcp import firestore_client
from common.response import json_response, parse_json_body
from common.storage import delete_gs_url, delete_s3_url, find_media_by_url


def handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return json_response(204, {})
    try:
        current_user(event)
        body = parse_json_body(event)
        deleted, failed = delete_media_by_urls(body.get("urls") or [])
        return json_response(200, {"deleted": deleted, "failed": failed})
    except Exception as exc:
        return json_response(500, {"error": str(exc)})


def delete_media_by_urls(urls):
    db = firestore_client()
    deleted = 0
    failed = []
    for url in urls:
        docs = find_media_by_url(db, url)
        if not docs:
            failed.append({"url": url, "reason": "No matching media"})
            continue
        for doc in docs:
            item = doc.to_dict()
            try:
                delete_s3_url(item.get("s3Url"))
                delete_gs_url(item.get("gcsUri"))
                delete_gs_url(item.get("thumbnailUrl"))
                for sorted_url in dict(item.get("sortedUrls") or {}).values():
                    delete_gs_url(sorted_url)
                if item.get("sha256"):
                    db.collection("checksums").document(item["sha256"]).delete()
                if item.get("thumbnailUrl"):
                    db.collection("thumbnailIndex").document(safe_id(item["thumbnailUrl"])).delete()
                doc.reference.delete()
                deleted += 1
            except Exception as exc:
                failed.append({"url": url, "reason": str(exc)})
    return deleted, failed
def safe_id(value):
    return value.replace("/", "_").replace(":", "_")
