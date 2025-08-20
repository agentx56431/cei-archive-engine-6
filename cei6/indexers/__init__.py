# Aggregator for indexer entry points.
# These names match the actual files in this folder: *_indexer.py

from .blogs_indexer import fetch_blogs_first_page
from .news_indexer import fetch_news_releases_first_page
from .opeds_indexer import fetch_opeds_first_page
from .studies_indexer import fetch_studies_first_page

__all__ = [
    "fetch_blogs_first_page",
    "fetch_news_releases_first_page",
    "fetch_opeds_first_page",
    "fetch_studies_first_page",
]
