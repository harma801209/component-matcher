"""Short-lived native Excel links. No member credentials enter the document URL."""

import base64
import hashlib
import hmac
import json
import re
import ssl
import time
import urllib.parse
import urllib.request

PUBLIC_ORIGIN = "https://fruition-component.pages.dev"
MAX_BYTES = 8 * 1024 * 1024
TTL_SECONDS = 300


def owner_key(session_token, api_secret):
    if not session_token or not api_secret:
        raise ValueError("authenticated session required")
    return hmac.new(api_secret.encode(), ("bom-excel:" + session_token).encode(), hashlib.sha256).hexdigest()


def _request(api_secret, method, payload):
    request = urllib.request.Request(
        PUBLIC_ORIGIN + "/api/bom-excel",
        data=json.dumps(payload, separators=(",", ":")).encode(),
        headers={"Authorization": "Bearer " + api_secret, "Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=12, context=ssl.create_default_context()) as response:
        return json.loads(response.read(16384))


def revoke(api_secret, owner):
    if not re.fullmatch(r"[a-f0-9]{64}", owner or ""):
        return
    # Idempotent, and safe to retry after an interrupted response.
    for attempt in range(2):
        try:
            _request(api_secret, "DELETE", {"owner": owner})
            return
        except Exception:
            if attempt:
                raise RuntimeError("temporary Excel link revocation unavailable") from None


def issue(api_secret, owner, data, filename):
    if not api_secret or not re.fullmatch(r"[a-f0-9]{64}", owner or ""):
        raise ValueError("authenticated session required")
    if not isinstance(data, bytes) or not data.startswith(b"PK\x03\x04") or len(data) > MAX_BYTES:
        raise ValueError("native Excel export unavailable; use download")
    result = _request(api_secret, "POST", {
        "owner": owner, "filename": filename,
        "dataBase64": base64.b64encode(data).decode("ascii"),
    })
    # Never launch a response-controlled arbitrary URL/protocol.
    url = str(result.get("url", ""))
    expiry = float(result.get("expiresAt", 0))
    if not re.fullmatch(re.escape(PUBLIC_ORIGIN) + r"/x/[A-Za-z0-9_-]{43}/BOM\.xlsx", url):
        raise ValueError("invalid document URL")
    if not time.time() < expiry <= time.time() + TTL_SECONDS + 10:
        raise ValueError("invalid document expiry")
    return {"url": url, "expires": expiry, "owner": owner,
            "digest": hashlib.sha256(data).hexdigest()}


def excel_uri(url):
    if not re.fullmatch(re.escape(PUBLIC_ORIGIN) + r"/x/[A-Za-z0-9_-]{43}/BOM\.xlsx", url or ""):
        return ""
    return "ms-excel:ofv|u|" + url
