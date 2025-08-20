# cei6/details/__init__.py
from __future__ import annotations

from typing import Iterable, List

from ..models import ListingItem
from .blogs_details import parse_blog_detail as fetch_blog_detail, BlogDetail


def fetch_blog_details_batch(
    items: Iterable[ListingItem],
    max_details: int | None = None,
) -> List[BlogDetail]:
    """
    Fetch blog details for a slice of listing items (blogs only).
    Respects max_details if provided.
    """
    out: List[BlogDetail] = []
    count = 0
    for it in items:
        if it.content_type != "blogs":
            # Only blogs are wired up right now
            continue
        if max_details is not None and count >= max_details:
            break
        try:
            detail = fetch_blog_detail(it.url)
            out.append(detail)
            count += 1
        except Exception as e:
            print(f"[warn] fetch detail failed (blogs): {it.url} :: {e}")
    return out
