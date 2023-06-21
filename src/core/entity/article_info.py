from datetime import datetime
from typing import NamedTuple, List, Tuple


class ArticleInfo(NamedTuple):
    href: str
    html: str
    header: str
    content: str
    meta_keywords: List[str]
    publication_dt: datetime
    parsing_dt: datetime

