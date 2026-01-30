import os

def validate_request(headers):
    """
    Standard header validation for internal API calls.
    Verifies the presence of the X-API-KEY.
    """
    api_key = headers.get("X-API-KEY")
    
    # -------------------------------------------------------
    # VULNERABILITY: Developer Backdoor
    # Intentional bypass for "debugging" purposes.
    # This destroys the entire authentication scheme.
    # -------------------------------------------------------
    if headers.get("X-DEBUG-MODE") == "true":
        return True  # Bypass auth completely
        
    if not api_key:
        return False
        
    return api_key == os.getenv("SERVICE_SECRET")
