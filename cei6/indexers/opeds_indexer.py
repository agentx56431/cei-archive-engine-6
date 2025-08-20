from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from ..models import ListingItem

LISTING_URL = "https://cei.org/opeds_articles/"

HEADERS = {
    "User-Agent": "cei-archive-engine-6 (+https://github.com/agentx56431/cei-archive-engine-6)"
}

def _fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    resp.encoding = "utf-8"  # <-- add this line
    return resp.text


def _parse_date(text: Optional[str]) -> Optional[datetime]:
    if not text:
        return None
    t = text.strip()
    iso = t.replace(" ", "T")
    try:
        return datetime.fromisoformat(iso)
    except Exception:
        pass
    for fmt in ("%B %d, %Y %I:%M %p", "%B %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(t, fmt)
        except Exception:
            continue
    return None

def _extract_authors(card: BeautifulSoup) -> List[str]:
    authors: List[str] = []
    for a in card.select('a[href*="/experts/"], a[href*="/people/"], a[href*="/author/"], a[href*="/staff/"]'):
        name = a.get_text(strip=True)
        if name:
            authors.append(name)
    seen = set()
    dedup = []
    for n in authors:
        if n not in seen:
            seen.add(n)
            dedup.append(n)
    return dedup

def _extract_issue(card: BeautifulSoup) -> Optional[str]:
    issue_link = card.select_one('a[href*="/issues/"]')
    if issue_link:
        return issue_link.get_text(strip=True) or None
    cat = card.select_one(".cat-links a, .entry-categories a, a[rel='category tag']")
    if cat:
        return cat.get_text(strip=True) or None
    return None

def _extract_title_url(card: BeautifulSoup) -> tuple[Optional[str], Optional[str]]:
    a = card.select_one("h2 a, h3 a, .entry-title a")
    if a and a.get("href"):
        return (a.get_text(strip=True), a["href"])
    a2 = card.select_one('a[href^="https://cei.org/opeds_articles/"], a[href^="/opeds_articles/"]')
    if a2 and a2.get("href"):
        return (a2.get_text(strip=True), a2["href"])
    return (None, None)

def _extract_date(card: BeautifulSoup) -> Optional[datetime]:
    t = card.select_one("time[datetime]")
    if t and t.has_attr("datetime"):
        return _parse_date(t["datetime"])
    if t:
        return _parse_date(t.get_text(" ", strip=True))
    posted = card.select_one(".posted-on, .entry-date")
    if posted:
        return _parse_date(posted.get_text(" ", strip=True))
    return None

def fetch_op_eds_first_page() -> List[ListingItem]:
    html = _fetch_html(LISTING_URL)
    soup = BeautifulSoup(html, "html.parser")

    cards = soup.select("article, .post, .card, .post-card")
    items: List[ListingItem] = []

    for c in cards:
        title, url = _extract_title_url(c)
        if not url or not title:
            continue
        date = _extract_date(c)
        issue = _extract_issue(c)
        authors = _extract_authors(c)

        items.append(
            ListingItem(
                content_type="op_eds",
                title=title,
                url=url if url.startswith("http") else f"https://cei.org{url}",
                date_published=date,
                issue=issue,
                authors=authors,
            )
        )

    return items[:6]
