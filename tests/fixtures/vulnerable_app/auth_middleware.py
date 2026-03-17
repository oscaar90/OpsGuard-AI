import os


def validate_request(headers):
    api_key = headers.get("X-API-KEY")

    # TODO: remove debug bypass before deploy
    if headers.get("X-DEBUG-MODE") == "true":
        return True  # Bypass auth completely

    if not api_key:
        return False

    return api_key == os.getenv("SERVICE_SECRET")
