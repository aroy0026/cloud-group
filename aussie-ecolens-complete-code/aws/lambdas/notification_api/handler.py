import os

import boto3

from common.auth import current_user
from common.gcp import firestore_client, server_timestamp
from common.response import json_response, parse_json_body

sns = boto3.client("sns")


def handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return json_response(204, {})
    try:
        user = current_user(event)
        path = event.get("rawPath") or event.get("path", "")
        body = parse_json_body(event)
        if path.endswith("/notifications/watch"):
            return json_response(200, create_watch(user, body))
        if path.endswith("/notifications/unwatch"):
            return json_response(200, disable_watch(user, body))
        if path.endswith("/notifications/publish"):
            return json_response(200, publish_internal(body))
        return json_response(404, {"error": f"Unknown notification route: {path}"})
    except Exception as exc:
        return json_response(500, {"error": str(exc)})


def create_watch(user, body):
    tag = normalize_tag(body.get("tag"))
    email = body.get("email") or user["email"]
    if not tag or not email:
        raise ValueError("tag and email are required")
    topic_arn = ensure_topic_for_tag(tag)
    sns.subscribe(TopicArn=topic_arn, Protocol="email", Endpoint=email)
    doc_id = f"{user['id']}_{tag}"
    firestore_client().collection("userWatches").document(doc_id).set(
        {
            "userId": user["id"],
            "email": email,
            "tag": tag,
            "snsTopicArn": topic_arn,
            "active": True,
            "updatedAt": server_timestamp(),
        },
        merge=True,
    )
    return {
        "tag": tag,
        "email": email,
        "snsTopicArn": topic_arn,
        "message": "Check your email and confirm the SNS subscription before demo.",
    }


def disable_watch(user, body):
    tag = normalize_tag(body.get("tag"))
    firestore_client().collection("userWatches").document(f"{user['id']}_{tag}").update(
        {"active": False, "updatedAt": server_timestamp()}
    )
    return {"tag": tag, "active": False}


def publish_internal(body):
    # Optional endpoint if Cloud Run calls AWS instead of holding SNS credentials.
    tag = normalize_tag(body["tag"])
    topic_arn = ensure_topic_for_tag(tag)
    sns.publish(
        TopicArn=topic_arn,
        Subject=f"Aussie EcoLens: new {tag} media",
        Message=body.get("message") or f"New media detected for watched tag {tag}",
    )
    return {"published": True}


def topic_for_tag(tag):
    prefix = os.environ["SNS_TOPIC_PREFIX"]
    # Example prefix: arn:aws:sns:ap-southeast-2:123456789012:aussie-ecolens-
    return f"{prefix}{tag}"


def ensure_topic_for_tag(tag):
    topic_arn = topic_for_tag(tag)
    topic_name = topic_arn.rsplit(":", 1)[-1]
    return sns.create_topic(Name=topic_name)["TopicArn"]


def normalize_tag(tag):
    return (tag or "").strip().lower().replace(" ", "_")
