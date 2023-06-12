from typing import Iterator

from src.core.entity.entities import ArticleInfoShort
from src.resources.scrapper import Scrapper


class RequestIterator:
    def __init__(self, scrapper: Scrapper, articles: list, page: int = 1) -> None:
        self._scrapper = scrapper
        self._page = page
        self._articles = list()
        if articles is not None:
            self._articles.extend(articles)
        self._index = 0

    def set_page(self, page: int) -> None:
        self._page = page

    def get_page(self) -> int:
        return self._page

    def _request_articles(self) -> list:
        articles = self._scrapper.scrape_list(self._page)
        self._page += 1
        return articles

    def clear(self) -> None:
        self._articles.clear()

    def __iter__(self) -> Iterator[ArticleInfoShort]:
        if len(self._articles) == 0:
            self._articles.extend(self._request_articles())
        for i in self._articles:
            yield i
            self._index += 1
            if self._index == len(self._articles) - 1:
                self._articles.extend(self._request_articles())