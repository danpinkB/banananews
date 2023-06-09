import pathlib
from abc import ABC, abstractmethod

from src.entity.entities import ArticleInfoShort, ArticleInfo
from src.helper.req_inspector import RequestInspector


class Parser(ABC):
    @abstractmethod
    def request_articles(self, page: int) -> list[ArticleInfoShort]:
        pass

    @abstractmethod
    def parse_article_info(self, html: str) -> ArticleInfo:
        pass

    @abstractmethod
    def request_article_info(self, slug: str) -> str:
        pass

    @abstractmethod
    def get_folder_path(self) -> pathlib.Path:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_inspector(self) -> RequestInspector:
        pass
