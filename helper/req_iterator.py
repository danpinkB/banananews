from typing import Generator, Dict, Any

from entity.entities import ArticleInfoShort
from helper.req_inspector import RequestInspector


class RequestIterator:
    def __init__(self, inspector: RequestInspector, articles: list, page: int = 1) -> None:
        self._inspector = inspector
        self._page = page
        self._articles = list()
        if articles is not None:
            self._articles.extend(articles)
        self._index = 0

    def set_page(self, page: int) -> None:
        self._page = page

    def get_page(self) -> int:
        return self._page

    def clear(self) -> None:
        self._articles.clear()

    def __iter__(self) -> Generator[ArticleInfoShort, None, None]:
        if len(self._articles) == 0:
            self._articles.extend(self._request_articles())
        for i in self._articles:
            yield i
            self._index += 1
            if self._index == len(self._articles) - 1:
                self._articles.extend(self._request_articles())

    def __next__(self) -> None:
        pass