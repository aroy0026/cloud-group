import base64
import os

import requests

from common.auth import current_user
from common.gcp import firestore_client
from common.response import json_response, parse_json_body
from common.storage import signed_gs_url, url_lookup_candidates


def handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return json_response(204, {})
    try:
        current_user(event)
        path = event.get("rawPath") or event.get("path", "")
        if path.endswith("/query/tags"):
            body = parse_json_body(event) if event.get("body") else {}
            return json_response(200, query_tags(body))
        if path.endswith("/query/species"):
            body = parse_json_body(event) if event.get("body") else {}
            return json_response(200, query_species(body))
        if path.endswith("/query/thumbnail"):
            body = parse_json_body(event) if event.get("body") else {}
            return json_response(200, query_thumbnail(body))
        if path.endswith("/query/file"):
            return json_response(200, query_uploaded_file(event))
        if "/media/" in path:
            media_id = path.rstrip("/").rsplit("/", 1)[-1]
            return json_response(200, get_media(media_id))
        return json_response(404, {"error": f"Unknown query route: {path}"})
    except Exception as exc:
        return json_response(500, {"error": str(exc)})


def query_tags(body):
    requested = {k.lower(): int(v) for k, v in body.get("tags", {}).items()}
    if not requested:
        return {"results": []}
    first_tag = next(iter(requested))
    db = firestore_client()
    candidates = (
        db.collection("media")
        .where("status", "==", "READY")
        .where("tagList", "array_contains", first_tag)
        .stream()
    )
    results = []
    for doc in candidates:
        item = doc.to_dict()
        counts = item.get("tags", {})
        if all(int(counts.get(tag, 0)) >= minimum for tag, minimum in requested.items()):
            results.append(media_result(item))
    return {"results": results}


def query_species(body):
    species = (body.get("species") or "").lower()
    if not species:
        return {"results": []}
    docs = (
        firestore_client()
        .collection("media")
        .where("status", "==", "READY")
        .where("tagList", "array_contains", species)
        .stream()
    )
    return {"results": [media_result(d.to_dict()) for d in docs]}


def query_thumbnail(body):
    thumb = body.get("thumbnailUrl")
    if not thumb:
        return {"fullImageUrl": None}
    db = firestore_client()
    for candidate in url_lookup_candidates(thumb):
        doc = db.collection("thumbnailIndex").document(safe_id(candidate)).get()
        if doc.exists:
            data = doc.to_dict()
            return {
                "fullImageUrl": sign_if_gs(data.get("fullImageUrl")),
                "canonicalFullImageUrl": data.get("fullImageUrl"),
            }
    return {"fullImageUrl": None, "canonicalFullImageUrl": None}


def get_media(media_id):
    doc = firestore_client().collection("media").document(media_id).get()
    if not doc.exists:
        return {"media": None}
    return {"media": media_result(doc.to_dict(), include_status=True)}


def query_uploaded_file(event):
    endpoint = os.environ.get("QUERY_FILE_PROCESSOR_URL")
    if not endpoint:
        raise ValueError("QUERY_FILE_PROCESSOR_URL is not configured")
    body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        payload = base64.b64decode(body)
    else:
        payload = body.encode("utf-8")
    # This endpoint detects tags only; it must not write a permanent media record.
    resp = requests.post(endpoint, data=payload, timeout=120)
    resp.raise_for_status()
    detected = resp.json().get("tags", {})
    return {"detectedTags": detected, "results": query_tags({"tags": detected})["results"]}


def media_result(item, include_status=False):
    result = {
        "mediaId": item.get("mediaId"),
        "fileKind": item.get("fileKind"),
        "originalName": item.get("originalName"),
        "contentType": item.get("contentType"),
        "tags": item.get("tags", {}),
        "tagList": item.get("tagList", []),
        "thumbnailUrl": sign_if_gs(item.get("thumbnailUrl")),
        "fullUrl": sign_if_gs(item.get("fullUrl") or item.get("gcsUri")),
        "canonicalThumbnailUrl": item.get("thumbnailUrl"),
        "canonicalFullUrl": item.get("fullUrl") or item.get("gcsUri"),
    }
    if include_status:
        result["status"] = item.get("status")
        result["error"] = item.get("error")
    return result


def sign_if_gs(url):
    if not url:
        return None
    if url.startswith("gs://"):
        return signed_gs_url(url)
    return url


def safe_id(value):
    return value.replace("/", "_").replace(":", "_")
