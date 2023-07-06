from datetime import datetime
from typing import NamedTuple, List, Tuple


class ArticleInfo(NamedTuple):
    id: str
    href: str
    html: str
    slug: str
    header: str
    content: str
    meta_keywords: List[str]
    publication_dt: datetime
    parsing_dt: datetime

