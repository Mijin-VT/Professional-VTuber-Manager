"""Twitter/X API v2 client using manual OAuth 1.0a signing.
Allows posting tweets without heavy external OAuth libraries.
"""

import time
import uuid
import hmac
import hashlib
import base64
import urllib.parse
import requests
import logging

logger = logging.getLogger("VTManager.Twitter")


def generate_oauth_header(
    method: str,
    url: str,
    params: dict,
    client_key: str,
    client_secret: str,
    resource_owner_key: str,
    resource_owner_secret: str
) -> str:
    """Generate OAuth 1.0a authorization header."""
    # 1. Gather all oauth parameters
    oauth_params = {
        "oauth_consumer_key": client_key,
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": resource_owner_key,
        "oauth_version": "1.0"
    }

    # Merge query/body params and oauth params (for JSON POST payloads, params is empty)
    all_params = {}
    all_params.update(params)
    all_params.update(oauth_params)

    # 2. Sort and encode parameters to build parameter string
    sorted_encoded_params = []
    for k in sorted(all_params.keys()):
        encoded_k = urllib.parse.quote(k, safe='')
        encoded_v = urllib.parse.quote(all_params[k], safe='')
        sorted_encoded_params.append(f"{encoded_k}={encoded_v}")
    parameter_string = "&".join(sorted_encoded_params)

    # 3. Create Signature Base String
    base_string = "&".join([
        method.upper(),
        urllib.parse.quote(url, safe=''),
        urllib.parse.quote(parameter_string, safe='')
    ])

    # 4. Create Signing Key
    signing_key = f"{urllib.parse.quote(client_secret, safe='')}&{urllib.parse.quote(resource_owner_secret, safe='')}".encode('utf-8')

    # 5. Calculate HMAC-SHA1 signature
    hashed = hmac.new(signing_key, base_string.encode('utf-8'), hashlib.sha1)
    signature = base64.b64encode(hashed.digest()).decode('utf-8')

    # Add signature to oauth parameters
    oauth_params["oauth_signature"] = signature

    # 6. Build Authorization header
    auth_header_parts = []
    for k in sorted(oauth_params.keys()):
        encoded_k = urllib.parse.quote(k, safe='')
        encoded_v = urllib.parse.quote(oauth_params[k], safe='')
        auth_header_parts.append(f'{encoded_k}="{encoded_v}"')

    return "OAuth " + ", ".join(auth_header_parts)


def post_tweet(
    text: str,
    client_key: str,
    client_secret: str,
    resource_owner_key: str,
    resource_owner_secret: str
) -> tuple[bool, str]:
    """Posts a tweet via Twitter API v2.

    Returns:
        (success, message_or_error)
    """
    url = "https://api.twitter.com/2/tweets"
    method = "POST"

    if not client_key or not client_secret or not resource_owner_key or not resource_owner_secret:
        return False, "Credenciales de Twitter incompletas."

    try:
        # For JSON body post, query params are empty for OAuth signing
        auth_header = generate_oauth_header(
            method=method,
            url=url,
            params={},
            client_key=client_key,
            client_secret=client_secret,
            resource_owner_key=resource_owner_key,
            resource_owner_secret=resource_owner_secret
        )

        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json"
        }
        payload = {"text": text}

        r = requests.post(url, json=payload, headers=headers, timeout=10.0)
        if r.status_code in [200, 201]:
            resp_data = r.json()
            tweet_id = resp_data.get("data", {}).get("id", "Unknown")
            return True, f"Tweet publicado con éxito (ID: {tweet_id})."
        else:
            try:
                err_detail = r.json().get("detail", r.text)
            except:
                err_detail = r.text
            logger.error("Twitter API error %s: %s", r.status_code, err_detail)
            return False, f"Error de la API de Twitter ({r.status_code}): {err_detail}"

    except Exception as e:
        logger.error("Failed to post tweet: %s", e)
        return False, f"Excepción al conectar con Twitter: {str(e)}"
