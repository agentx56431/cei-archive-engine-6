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
    """
    Append unseen listing items (dedup by URL) to outputs/index/{type}.jsonl.
    Returns number of new lines written.
    """
    ensure_output_dirs()
    path = jsonl_path_for(content_type)
    seen = _load_existing_urls(path)
    new = [it for it in items if it.url not in seen]

    if not new:
        return 0

    with path.open("a", encoding="utf-8") as f:
        for it in new:
            f.write(json.dumps(it.to_dict(), ensure_ascii=False) + "\n")

    return len(new)
