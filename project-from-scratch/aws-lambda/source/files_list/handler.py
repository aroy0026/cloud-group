from common.core import current_user, handle_options, list_owner_media, response


def handler(event, context):
    options = handle_options(event)
    if options:
        return options
    try:
        user = current_user(event)
        return response(200, list_owner_media(user["id"]))
    except Exception as exc:
        return response(500, {"error": str(exc)})
