import pathlib
from datetime import datetime

from bs4 import BeautifulSoup

from entity.entities import ArticleInfo, ArticleInfoShort
from error.errors import RequestError, ContentParsingError
from helper.req_inspector import RequestInspector
from parser.base_parser import Parser

ARTICLES_REQ_URL = "https://cryptopotato.com/category/crypto-news/page/"
CONCRETE_ARTICLE_URL = "https://cryptopotato.com/"


class PotatoParser(Parser):
    def __init__(self, inspector: RequestInspector, folder_path: pathlib.Path = None):
        self._inspector = inspector
        if folder_path is None:
            self._path = pathlib.Path(f'./uploads/crypto_potato')
        else:
            self._path = folder_path

    def request_articles(self, page: int) -> list[ArticleInfoShort]:
        try:
            resp = self._inspector.request_get(f"{ARTICLES_REQ_URL}{page}", {})
            bs_ = BeautifulSoup(resp.text, "html.parser")
            articles = list()
            for i in bs_.select("article"):
                article_date = i.select_one("div.entry-meta")
                articles.append(ArticleInfoShort(
                    id=i['id'].split("-")[1],
                    timestamp=datetime.strptime(article_date.select_one("time")['datetime'] +
                                                " " + article_date.select_one("span.entry-time").text,
                                                "%Y-%m-%d %H:%M").timestamp())
                )
            return articles
        except RequestError:
            return list()

    def parse_article_info(self, html: str) -> ArticleInfo:
        bs_ = BeautifulSoup(html, "html.parser")
        try:
            article = bs_.select_one("div.entry-post")
            info = ArticleInfo(
                header=article.select_one("div.page-title").text,
                content=article.select_one("div.coincodex-content").text,
                publication_dt=datetime.strptime(article.select_one("span.last-modified-timestamp").text,
                                                 "%b %d, %Y @ %H:%M"),
                parsing_dt=datetime.now(),
                html=html,
                href=bs_.select_one("meta[property='og:url']")["content"],
                meta_keywords=[i['content'] for i in
                               bs_.findAll(lambda tag: tag.name == "meta" and tag.has_attr("property"))],
            )
            return info
        except TypeError:
            raise ContentParsingError("some article element wasn't found")

    def request_article_info(self, slug: str) -> str:
        return self._inspector.request_get(f"{CONCRETE_ARTICLE_URL}", {"p": slug}).text

    def get_folder_path(self) -> pathlib.Path:
        return self._path

    def get_name(self) -> str:
        return "crypto_potato"

    def get_inspector(self) -> RequestInspector:
        return self._inspector
