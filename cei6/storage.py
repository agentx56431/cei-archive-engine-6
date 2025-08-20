# cei6/storage.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Set

from .models import ListingItem

BASE_OUT = Path("outputs") / "index"

def ensure_output_dirs() -> None:
    BASE_OUT.mkdir(parents=True, exist_ok=True)

def jsonl_path_for(content_type: str) -> Path:
    # one rolling JSONL per type, easy to merge later
    return BASE_OUT / f"{content_type}.jsonl"

def _load_existing_urls(p: Path) -> Set[str]:
    urls: Set[str] = set()
    if not p.exists():
        return urls
    # Safe/forgiving read of JSONL; skip bad lines.
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                url = obj.get("url")
                if isinstance(url, str):
                    urls.add(url)
            except Exception:
                # ignore malformed lines
                continue
    return urls

def write_index_jsonl(content_type: str, items: Iterable[ListingItem]) -> int:
    ensure_output_dirs()
    path = jsonl_path_for(content_type)

    # --- SAFETY GUARD ---
    items = list(items)
    if items and isinstance(items[0], str):
        raise TypeError(
            "write_index_jsonl expected ListingItem objects but got strings. "
            "Did you call it with arguments reversed? "
            "Use write_index_jsonl(content_type, items)."
        )
    # ---------------------

    seen = _load_existing_urls(path)
    new = [it for it in items if it.url not in seen]

    if not new:
        return 0

    with path.open("a", encoding="utf-8") as f:
        for it in new:
            f.write(json.dumps(it.to_dict(), ensure_ascii=False) + "\n")

    return len(new)

from typing import Iterable
from .models import DetailRecord
import json
import os

def _ensure_details_dir() -> str:
    base = os.path.join("outputs", "details")
    os.makedirs(base, exist_ok=True)
    return base

def write_details_jsonl(records: Iterable[DetailRecord], type_name: str) -> int:
    """Append details to outputs/details/{type}.jsonl, de-dup by URL."""
    base = _ensure_details_dir()
    path = os.path.join(base, f"{type_name}.jsonl")
    # Load existing URLs to avoid dupes
    existing = set()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict) and "url" in obj:
                        existing.add(obj["url"])
                except Exception:
                    pass

    written = 0
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        for rec in records:
            if rec.url in existing:
                continue
            f.write(json.dumps(rec.to_json_obj(), ensure_ascii=False) + "\n")
            existing.add(rec.url)
            written += 1
    return written
