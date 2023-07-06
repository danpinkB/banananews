from datetime import datetime
from enum import Enum
from typing import NamedTuple, Optional

from . import ArticleInfoShort, ArticleInfo
from .parse_resource_recipe import TagRecipe, ElementRecipe
from ..error import ContentParsingError


class DriverType(Enum):
    SELENIUM = 1
    REQUEST = 2


class PagerType(Enum):
    NONE = 0,
    SELECTOR = 1,
    SIMPLE = 2,
    SELENIUM = 3


class ReactorSettings(NamedTuple):
    hour_limit: int
    href: str
    is_binary_search: bool
    pager_type: PagerType
    next_page: Optional[TagRecipe]
    prev_page: Optional[TagRecipe]
    list_driver: DriverType
    page_driver: Optional[DriverType]
    list_recipe: ElementRecipe
    article_short_info_recipe: ElementRecipe
    article_info_recipe: Optional[ElementRecipe]

    def parse_articles(self, html: str) -> list[ArticleInfoShort]:
        parsed_articles_html = self.list_recipe.parse_data(html)
        articles = list()
        for article_html in parsed_articles_html.get("articles"):
            parsed_article = self.article_short_info_recipe.parse_data(article_html)
            articles.append(ArticleInfoShort(
                id=parsed_article.get("id"),
                href=parsed_article.get("href"),
                timestamp=parsed_article.get("datetime").timestamp()
            ))
        return articles

    def parse_article(self, html: str) -> ArticleInfo:
        try:
            parsed_article = self.article_info_recipe.parse_data(html)
            return ArticleInfo(
                id=parsed_article.get("id"),
                href=parsed_article.get("href"),
                parsing_dt=datetime.now(),
                content=parsed_article.get("content"),
                header=parsed_article.get("header"),
                publication_dt=parsed_article.get("publication_dt"),
                meta_keywords=parsed_article.get("meta_keywords"),
                slug=parsed_article.get("slug"),
                html=html
            )
        except KeyError as err:
            raise ContentParsingError(f"an error while parsing article href - {err}")

