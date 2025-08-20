# cei6/storage.py
from __future__ import annotations

import json
import os
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Iterable, Union, Any

# Paths
PKG_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(PKG_DIR)
OUT_INDEX_DIR = os.path.join(ROOT_DIR, "outputs", "index")
OUT_DETAILS_DIR = os.path.join(ROOT_DIR, "outputs", "details")


def ensure_output_dirs() -> None:
    os.makedirs(OUT_INDEX_DIR, exist_ok=True)
    os.makedirs(OUT_DETAILS_DIR, exist_ok=True)


def _jsonl_path(kind: str, type_name: str) -> str:
    ensure_output_dirs()
    base = OUT_INDEX_DIR if kind == "index" else OUT_DETAILS_DIR
    return os.path.join(base, f"{type_name}.jsonl")


def _iter_existing_urls(path: str) -> set[str]:
    seen: set[str] = set()
    if not os.path.exists(path):
        return seen
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                url = obj.get("url")
                if url:
                    seen.add(url)
            except Exception:
                # ignore malformed lines
                continue
    return seen


def _to_record(obj: Any) -> dict:
    # Accept dataclass, dict, or any object with the expected attributes
    if is_dataclass(obj):
        d = asdict(obj)
    elif isinstance(obj, dict):
        d = dict(obj)
    else:
        d = {}
        for key in (
            "content_type",
            "title",
            "url",
            "date_published",
            "issue",
            "authors",
            "outlet",
            "outlet_url",
            "documents",
            "content",
            "paragraphs",
        ):
            if hasattr(obj, key):
                d[key] = getattr(obj, key)

    # normalize date
    dp = d.get("date_published")
    if isinstance(dp, datetime):
        d["date_published"] = dp.isoformat()

    # normalize authors to list[str]
    if "authors" in d:
        if isinstance(d["authors"], str):
            d["authors"] = [a.strip() for a in d["authors"].split(",") if a.strip()]
        elif not isinstance(d["authors"], list) and d["authors"] is not None:
            d["authors"] = [str(d["authors"])]

    return d


def write_index_jsonl(arg1: Any, arg2: Any) -> int:
    """
    Order-agnostic:
    - write_index_jsonl(type_name: str, items: Iterable)
    - write_index_jsonl(items: Iterable, type_name: str)
    """
    if isinstance(arg1, str) and not isinstance(arg2, str):
        type_name, items = arg1, arg2
    elif isinstance(arg2, str) and not isinstance(arg1, str):
        type_name, items = arg2, arg1
    else:
        raise TypeError(
            "write_index_jsonl expects (type_name:str, items) or (items, type_name:str)"
        )

    path = _jsonl_path("index", type_name)
    seen = _iter_existing_urls(path)

    new_items = []
    for it in items or []:
        url = None
        try:
            url = it["url"] if isinstance(it, dict) else getattr(it, "url", None)
        except Exception:
            url = None
        if not url or url in seen:
            continue
        new_items.append(it)

    if not new_items:
        return 0

    written = 0
    with open(path, "a", encoding="utf-8", newline="") as f:
        for it in new_items:
            rec = _to_record(it)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1
    return written


def write_detail_jsonl(arg1: Any, arg2: Any) -> int:
    """
    Order-agnostic:
    - write_detail_jsonl(type_name: str, detail)
    - write_detail_jsonl(detail, type_name: str)
    """
    if isinstance(arg1, str) and not isinstance(arg2, str):
        type_name, detail = arg1, arg2
    elif isinstance(arg2, str) and not isinstance(arg1, str):
        type_name, detail = arg2, arg1
    else:
        raise TypeError(
            "write_detail_jsonl expects (type_name:str, detail) or (detail, type_name:str)"
        )

    path = _jsonl_path("details", type_name)
    seen = _iter_existing_urls(path)

    rec = _to_record(detail)
    url = rec.get("url")
    if not url or url in seen:
        return 0

    with open(path, "a", encoding="utf-8", newline="") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return 1
