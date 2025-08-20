from __future__ import annotations
from typing import Dict, List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

def _norm(s: str | None) -> str:
    return " ".join((s or "").split())

def fetch_blog_detail(url: str) -> Dict:
    """
    Fetch a CEI blog detail page and return:
      { "url", "title", "paragraphs": [...], "pdf_links": [...] }
    We intentionally do NOT try to re-derive date/issue/authors here—
    we trust the index for those to avoid mismatch.
    """
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    main = soup.select_one("main.site-main") or soup
    article = main.select_one("article") or main

    # Title
    h1 = main.select_one("h1")
    title = _norm(h1.get_text(strip=True)) if h1 else ""

    # Paragraphs (skip empty)
    paragraphs: List[str] = []
    for p in article.select("p"):
        txt = _norm(p.get_text(" ", strip=True))
        if txt:
            paragraphs.append(txt)

    # PDF links
    pdfs: List[str] = []
    for a in article.select('a[href$=".pdf"], a[href*=".pdf?"]'):
        href = (a.get("href") or "").strip()
        if href:
            pdfs.append(urljoin(url, href))

    # Unique + stable order
    seen = set()
    pdf_links = []
    for p in pdfs:
        if p not in seen:
            seen.add(p)
            pdf_links.append(p)

    return {
        "url": url,
        "title": title,
        "paragraphs": paragraphs,
        "pdf_links": pdf_links,
    }
