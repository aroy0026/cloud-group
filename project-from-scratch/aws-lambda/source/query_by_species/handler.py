from common.core import current_user, handle_options, list_owner_media, parse_body, response


def handler(event, context):
    options = handle_options(event)
    if options:
        return options
    try:
        user = current_user(event)
        species = (parse_body(event).get("species") or "").strip().lower()
        results = [
            item
            for item in list_owner_media(user["id"])
            if any(species in tag["name"].lower() for tag in item.get("tags", []))
        ]
        return response(200, results)
    except Exception as exc:
        return response(500, {"error": str(exc)})
