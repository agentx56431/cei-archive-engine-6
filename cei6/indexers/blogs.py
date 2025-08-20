# cei6/indexers/blogs.py
from __future__ import annotations
from typing import List, Set, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import re

from ..http import fetch_html
from .base import IndexRow

BASE = "https://cei.org"
LIST_URL = "https://cei.org/blog/"

def _clean(s: Optional[str]) -> str:
    if not s:
        return ""
    return " ".join(s.split())

def _looks_like_post(href: str) -> bool:
    # accept /blog/<slug>/ but ignore /blog/page/<n>/ and query pagination
    return (
        href.startswith("/blog/") and
        "/page/" not in href and
        "posts_per_page" not in href and
        href.count("/") >= 3  # crude: /blog/<slug>/
    )

def _first_text(el, selector: str) -> str:
    m = el.select_one(selector)
    return _clean(m.get_text(strip=True)) if m else ""

def _find_issue(container) -> str:
    # often an <a href="/issues/...">Issue Name</a>
    for a in container.select("a[href]"):
        href = a.get("href", "")
        if "/issues/" in href:
            t = _clean(a.get_text(strip=True))
            if t:
                return t
    return ""

def _find_authors(container) -> list[str]:
    # best-effort: look for rel=author, or classes with author/byline
    names: list[str] = []
    for a in container.select('a[rel="author"], .author a, .byline a, .by-author a'):
        t = _clean(a.get_text(strip=True))
        if t and t not in names:
            names.append(t)
    # if nothing, try plain text in nodes with author-ish classes
    if not names:
        for el in container.select(".author, .byline, .posted-by"):
            t = _clean(el.get_text(" ", strip=True))
            # strip "By " prefixes
            t = re.sub(r"^\s*by\s+", "", t, flags=re.I)
            if t and t.lower() != "by":
                # split on commas/“and”
                parts = re.split(r",| and ", t)
                for p in parts:
                    p = _clean(p)
                    if p and p not in names:
                        names.append(p)
    return names

def fetch_first_page() -> List[IndexRow]:
    html, final_url = fetch_html(LIST_URL)
    soup = BeautifulSoup(html, "lxml")

    # Gather candidate post links
    seen: Set[str] = set()
    rows: List[IndexRow] = []

    for a in soup.select("a[href]"):
        href = a.get("href", "")
        # normalize to absolute:
        abs_url = urljoin(BASE, href)
        # only keep cei.org links that look like posts
        if not abs_url.startswith(BASE):
            continue
        path = abs_url.replace(BASE, "", 1)
        if not _looks_like_post(path):
            continue
        if abs_url in seen:
            continue
        seen.add(abs_url)

        # find a card container to mine meta (date/issue/author)
        container = a.find_parent(["article", "li", "div"]) or soup
        title = _clean(a.get_text(strip=True))
        if not title:
            # try common title holders in the container
            title = (_first_text(container, "h2, h3, .entry-title, .c-card__title") or
                     _clean(a.get("title")) or abs_url)

        # date (best effort: <time datetime>, or text in <time>)
        date = ""
        t = container.select_one("time[datetime]")
        if t and t.get("datetime"):
            date = _clean(t["datetime"])
        elif t:
            date = _clean(t.get_text(strip=True))

        issue = _find_issue(container)
        authors = _find_authors(container)

        rows.append(IndexRow(
            source_type="blogs",
            url=abs_url,
            title=title,
            date_published=date,
            issue=issue,
            authors=authors or [],
        ))

    # Keep only the first 30 unique posts (typical first page volume)
    return rows[:30]
