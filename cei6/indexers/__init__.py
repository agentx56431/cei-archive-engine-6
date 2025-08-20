# cei6/indexers/__init__.py
from .blogs import fetch_first_page as fetch_blogs_first_page
from .news_releases import fetch_first_page as fetch_news_releases_first_page
from .op_eds import fetch_first_page as fetch_op_eds_first_page
from .studies import fetch_first_page as fetch_studies_first_page

__all__ = [
    "fetch_blogs_first_page",
    "fetch_news_releases_first_page",
    "fetch_op_eds_first_page",
    "fetch_studies_first_page",
]
