from common.core import current_user, handle_options, parse_body, response, settings_table


def handler(event, context):
    options = handle_options(event)
    if options:
        return options
    try:
        user = current_user(event)
        method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod")
        if method == "GET":
            settings = settings_table().get_item(Key={"ownerId": user["id"]}).get("Item") or {}
            return response(200, {"settings": settings.get("settings") or {"emailOn": True, "thumbOn": True}})
        settings = parse_body(event)
        settings_table().put_item(Item={"ownerId": user["id"], "settings": settings})
        return response(200, {"settings": settings})
    except Exception as exc:
        return response(500, {"error": str(exc)})
