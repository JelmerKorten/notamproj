"""Gmail OAuth2 (XOAUTH2) support for the emailer.

Gmail retired plain app passwords for some accounts, so SMTP auth can instead
use a short-lived OAuth2 access token via the SASL ``XOAUTH2`` mechanism
(Gmail docs: /workspace/gmail/imap/xoauth2-protocol).

Token handling here is deliberately stdlib-only at runtime:

* ``refresh_access_token`` exchanges a long-lived *refresh* token for a
  short-lived *access* token (POST to ``oauth2.googleapis.com/token``).
  The refresh token is stored in configuration / environment / CI secrets
  and is never logged or committed.
* ``xoauth2_string`` builds the exact SASL initial-response format Gmail
  requires: ``base64("user=..^Aauth=Bearer ..^A^A")``.

The access token (default 1h lifetime) is obtained fresh on every send and is
only used over TLS.
"""

import json
import urllib.error
import urllib.parse
import urllib.request

GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
SCOPE_GMAIL_SMTP = "https://mail.google.com/"


class OAuthTokenError(RuntimeError):
    """Raised when the Google token endpoint rejects or misanswers a request."""


def xoauth2_string(user: str, access_token: str) -> str:
    """Return the raw SASL XOAUTH2 initial response for ``user`` + ``access_token``.

    The returned string is not base64-encoded; ``smtplib.auth`` base64-encodes
    whatever the auth callable returns.
    """
    return f"user={user}\x01auth=Bearer {access_token}\x01\x01"


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    """Exchange a refresh token for a fresh access token.

    Raises :class:`OAuthTokenError` on HTTP errors or a missing ``access_token``
    in the response. No credentials are ever logged.
    """
    form = urllib.parse.urlencode(
        {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        }
    ).encode("ascii")
    request = urllib.request.Request(GOOGLE_TOKEN_URI, data=form, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise OAuthTokenError(f"token refresh failed (HTTP {exc.code})") from exc
    token = payload.get("access_token")
    if not token:
        raise OAuthTokenError("token refresh failed: no access_token in response")
    return token
