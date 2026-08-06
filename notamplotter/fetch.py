"""Fetching of raw NOTAM data from the FAA NOTAM search API.

Phase 3 (AGENT_PLAN.md): replaces the legacy Selenium scrapers with a
``curl_cffi``-based :class:`FaaClient`.

``curl_cffi`` (not plain ``requests``) is required: the endpoint is protected
by Akamai TLS fingerprinting which returns HTTP 403 to vanilla HTTP clients.
The session must first ``GET`` the base URL so Akamai issues its cookies, then
``POST`` form-encoded search queries. Results are paginated via ``offset`` in
pages of 30.
"""

import os
import re
import time
from datetime import date

from curl_cffi import requests as creq

from notamplotter._logging import get_logger

logger = get_logger(__name__)

_DEFAULT_BASE_URL = "https://notams.aim.faa.gov/notamSearch"
_TIMEOUT = 30
_RETRIES = 3
_PAGE_SIZE = 30

# ICAO location indicators / designators are purely alphanumeric (e.g. OMAA,
# KZLA, HE24). Restricting input here blocks path traversal, SMTP header
# injection and HTML/script injection through airport codes.
_ICAO_RE = re.compile(r"^[A-Za-z0-9]{1,8}$")


def _normalize_designators(airports: str | list[str]) -> list[str]:
    """Return uppercase ICAO codes from a string or list of airport inputs.

    Raises :class:`ValueError` if any token is not a valid ICAO code, so
    user-supplied codes can never reach file paths or the HTML title.
    """
    if isinstance(airports, str):
        parts = re.split(r"[\s_,]+", airports.strip())
    else:
        parts = list(airports)
    normalized = []
    for part in parts:
        code = part.strip().upper()
        if not code:
            continue
        if not _ICAO_RE.match(code):
            raise ValueError(f"invalid airport code: {code!r}")
        normalized.append(code)
    return normalized


class FaaClient:
    """Client for the public FAA NOTAM search API."""

    def __init__(self, base_url: str | None = None, timeout: int = _TIMEOUT, retries: int = _RETRIES) -> None:
        self.base_url = (base_url or os.environ.get("FAA_API_BASE_URL") or _DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self._session = creq.Session(impersonate="chrome")

    def _get_cookies(self) -> None:
        """Warm up the session with a GET so Akamai issues its cookies."""
        for attempt in range(self.retries):
            try:
                response = self._session.get(f"{self.base_url}/", timeout=self.timeout)
                response.raise_for_status()
                logger.debug("FAA session cookies acquired")
                return
            except Exception as exc:  # noqa: BLE001 -- retried network/HTTP failures
                if attempt == self.retries - 1:
                    raise
                self._backoff(attempt, exc)

    def _search_page(self, designators: list[str], offset: int) -> dict:
        """POST a single search page request and return the parsed JSON dict."""
        payload = {
            "searchType": "0",
            "designatorsForLocation": ",".join(designators),
            "offset": str(offset),
            "notamsOnly": "false",
        }
        for attempt in range(self.retries):
            try:
                response = self._session.post(
                    f"{self.base_url}/search",
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
            except Exception as exc:  # noqa: BLE001 -- retried network/HTTP failures
                if attempt == self.retries - 1:
                    raise
                self._backoff(attempt, exc)
        return {}

    def _backoff(self, attempt: int, exc: Exception) -> None:
        wait = 2**attempt
        logger.warning("FAA API request failed (%s); retrying in %ss", exc, wait)
        time.sleep(wait)

    def search(self, designators: list[str] | str, offset: int = 0) -> dict:
        """Fetch one page of NOTAMs for ``designators`` starting at ``offset``."""
        if not self._session.cookies:
            self._get_cookies()
        return self._search_page(_normalize_designators(designators), offset)

    def fetch_all(self, designators: list[str] | str) -> list[dict]:
        """Fetch every page of NOTAMs for ``designators`` and return the list."""
        if not self._session.cookies:
            self._get_cookies()
        designators = _normalize_designators(designators)
        all_notams = []
        offset = 0
        while True:
            page = self._search_page(designators, offset)
            notams = page.get("notamList") or []
            all_notams.extend(notams)
            total = page.get("totalNotamCount") or 0
            next_offset = page.get("endRecordCount") or offset + len(notams)
            if not notams or next_offset >= total:
                break
            offset = next_offset
        logger.info("fetched %d notams", len(all_notams))
        return all_notams


def fetch_notams(designators: list[str] | str, client: FaaClient | None = None) -> list[dict]:
    """Fetch all NOTAMs for ``designators`` and return the raw ``notamList``."""
    client = client or FaaClient()
    return client.fetch_all(designators)


def collect(base, airports: str | list[str], client: FaaClient | None = None) -> str:
    """Fetch NOTAMs for ``airports`` and write them to ``files/{today}_notams_*.csv``.

    Returns the path of the written file. Blocks are stored verbatim from the
    API ``icaoMessage`` field, separated by blank lines, so the file can be
    re-read with :func:`notamplotter.parse.readnotams`.
    """
    today = date.today().strftime("%Y%m%d")
    airports_str = "_".join(code.lower() for code in _normalize_designators(airports))
    client = client or FaaClient()
    notams = client.fetch_all(_normalize_designators(airports))

    filepath = os.path.join(base, "files", f"{today}_notams_{airports_str}.csv")
    with open(filepath, "w") as file:
        for notam in notams:
            file.write((notam.get("icaoMessage") or "").strip())
            file.write("\n\n")
    logger.info("csv file created: %s", filepath)
    return filepath
