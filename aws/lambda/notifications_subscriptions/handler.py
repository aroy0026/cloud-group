import os

from common.core import clean_tag, current_user, handle_options, parse_body, response, sns, subscriptions_table


def handler(event, context):
    options = handle_options(event)
    if options:
        return options
    try:
        user = current_user(event)
        method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod")
        if method == "GET":
            return response(200, {"tags": get_tags(user["id"])})
        body = parse_body(event)
        tag = clean_tag(body.get("tag"))
        if not tag:
            return response(400, {"error": "tag is required"})
        if method == "DELETE":
            tags = [item for item in get_tags(user["id"]) if item != tag]
            save_tags(user["id"], tags)
            return response(200, {"tags": tags})
        tags = sorted(set(get_tags(user["id"]) + [tag]))
        save_tags(user["id"], tags)
        subscribe_email_if_configured(tag, user.get("email"))
        return response(200, {"tags": tags})
    except Exception as exc:
        return response(500, {"error": str(exc)})


def get_tags(owner_id):
    item = subscriptions_table().get_item(Key={"ownerId": owner_id}).get("Item") or {}
    return item.get("tags") or []


def save_tags(owner_id, tags):
    subscriptions_table().put_item(Item={"ownerId": owner_id, "tags": tags})


def subscribe_email_if_configured(tag, email):
    prefix = os.environ.get("SNS_TOPIC_PREFIX")
    if not prefix or not email:
        return
    topic_arn = sns.create_topic(Name=f"{prefix}{tag}")["TopicArn"] if not prefix.startswith("arn:") else f"{prefix}{tag}"
    sns.subscribe(TopicArn=topic_arn, Protocol="email", Endpoint=email)
