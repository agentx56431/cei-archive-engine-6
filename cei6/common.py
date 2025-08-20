from __future__ import annotations
import time
from typing import Optional
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

# One session for all requests, with retries + desktop UA.
_session: Optional[requests.Session] = None

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

def _get_session() -> requests.Session:
    global _session
    if _session is None:
        s = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET", "HEAD"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        s.headers.update(HEADERS)
        _session = s
    return _session

def fetch_html(url: str, timeout: int = 20) -> str:
    s = _get_session()
    resp = s.get(url, timeout=timeout)
    if resp.status_code == 403:
        # tiny courtesy backoff + 1 retry with same session
        time.sleep(0.75)
        resp = s.get(url, timeout=timeout)
    resp.raise_for_status()
    # Some CEI pages can be mis-encoded; requests handles most.
    return resp.text

def get_soup(url: str, timeout: int = 20) -> BeautifulSoup:
    html = fetch_html(url, timeout=timeout)
    return BeautifulSoup(html, "html.parser")
