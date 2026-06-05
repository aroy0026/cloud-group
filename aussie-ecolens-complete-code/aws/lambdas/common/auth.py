def claims_from_event(event):
    authorizer = event.get("requestContext", {}).get("authorizer", {})
    claims = authorizer.get("claims") or authorizer.get("jwt", {}).get("claims") or {}
    return claims


def current_user(event):
    claims = claims_from_event(event)
    sub = claims.get("sub")
    if not sub:
        raise ValueError("Authenticated Cognito sub claim missing")
    return {
        "id": sub,
        "email": claims.get("email", ""),
        "firstName": claims.get("given_name", ""),
        "lastName": claims.get("family_name", ""),
    }

