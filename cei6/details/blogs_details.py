# cei6/details/blogs_details.py
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional

import requests
from bs4 import BeautifulSoup


@dataclass
class BlogDetail:
    content_type: str  # "blogs"
    url: str
    title: str
    date_published: Optional[str]
    issue: Optional[str]
    authors: List[str]
    content: str
    paragraphs: List[str]
    documents: List[str]


def _make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            # Use a real UA to avoid 403 blocks
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://cei.org/blog/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    )
    return s


def _fetch_html(url: str, session: requests.Session) -> str:
    # One retry on 403/5xx
    for attempt in range(2):
        resp = session.get(url, timeout=20)
        if resp.status_code == 200:
            return resp.text
        if resp.status_code in (403, 429, 500, 502, 503):
            time.sleep(1.0)  # tiny backoff
            continue
        resp.raise_for_status()
    # last attempt failed
    resp.raise_for_status()
    return ""  # never reached


def parse_blog_detail(url: str) -> BlogDetail:
    session = _make_session()
    html = _fetch_html(url, session)
    soup = BeautifulSoup(html, "html.parser")

    # Title
    title_el = soup.find(["h1", "h2"], class_="entry-title") or soup.find("h1")
    title = (title_el.get_text(strip=True) if title_el else "").strip()

    # Header area: author/date/issue often live here on CEI posts
    header = soup.find(class_="entry-meta") or soup.find("header")
    authors: List[str] = []
    date_published: Optional[str] = None
    issue: Optional[str] = None

    if header:
        # authors: find links with /experts/ or rel="author"
        author_links = header.select('a[href*="/experts/"], a[rel="author"]')
        for a in author_links:
            name = a.get_text(strip=True)
            if name:
                authors.append(name)

        # date: <time> or text like "August 12, 2025"
        time_el = header.find("time")
        if time_el and time_el.has_attr("datetime"):
            date_published = time_el["datetime"]
        elif time_el:
            date_published = time_el.get_text(strip=True)

        # issue: look for a visible label/badge near meta
        issue_el = header.find(class_="badge") or header.find(class_="entry-category")
        if issue_el:
            issue = issue_el.get_text(" ", strip=True)

    # Content & paragraphs
    # Most CEI single posts wrap content in .entry-content or .post-content
    content_root = soup.find(class_="entry-content") or soup.find(class_="post-content") or soup
    paras: List[str] = []
    for p in content_root.find_all("p"):
        txt = p.get_text(" ", strip=True)
        if txt:
            paras.append(txt)

    content = "\n\n".join(paras)

    # Any documents/PDF links?
    documents: List[str] = []
    for a in content_root.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".pdf"):
            documents.append(href)

    return BlogDetail(
        content_type="blogs",
        url=url,
        title=title,
        date_published=date_published,
        issue=issue,
        authors=authors,
        content=content,
        paragraphs=paras,
        documents=documents,
    )
