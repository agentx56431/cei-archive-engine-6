# cei6/http.py
from __future__ import annotations
from typing import Tuple
import requests

HEADERS = {
    "User-Agent": "CEI6/0.1 (+https://github.com/yourname/cei-archive-engine-6)"
}

def fetch_html(url: str, timeout: int = 20) -> Tuple[str, str]:
    """
    Returns (html_text, final_url).
    Raises requests.HTTPError for non-200 responses.
    """
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    # requests guesses encoding; keep its guess
    return resp.text, str(resp.url)
