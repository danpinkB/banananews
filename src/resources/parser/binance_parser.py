import pathlib
from datetime import datetime

from bs4 import BeautifulSoup

from src.core.entity.entities import ArticleInfoShort, ArticleInfo
from src.core.error.errors import RequestError, ContentParsingError
from src.resources.helper.req_inspector import RequestInspector

ARTICLES_REQ_URL = "https://www.binance.com/bapi/composite/v1/public/cms/news/queryFlashNewsList"
CONCRETE_ARTICLE_URL = "https://www.binance.com/en/news/flash/"


class BinanceParser:
    def __init__(self, inspector: RequestInspector, folder_path: pathlib.Path = None):
        self._inspector = inspector
        if folder_path is None:
            self._path = pathlib.Path(f'./uploads/binance')
        else:
            self._path = folder_path

    def request_articles(self, page: int) -> list[ArticleInfoShort]:
        try:
            res = self._inspector \
                .request_get(ARTICLES_REQ_URL, {"pageNo": page, "pageSize": 20, "isTransform": "false", "tagId": ""}) \
                .json() \
                .get("data") \
                .get("contents")
            if res is not None:
                return [ArticleInfoShort(id=i['id'], timestamp=i['createTime']/1000) for i in res]
            return list()
        except RequestError:
            return list()

    def parse_article_info(self, html: str) -> ArticleInfo:
        bs_ = BeautifulSoup(html, "html.parser")
        try:
            article = bs_.select_one("html > article.css-17l2a77 > ")
            info = ArticleInfo(
                header=article.select_one("h1.css-ps28d1").text,
                content=article.select_one("div.css-13uwx4b").text,
                publication_dt=datetime.strptime(article.select_one("div.css-1hmgk20").text, "%Y-%m-%d %H:%M"),
                parsing_dt=datetime.now(),
                html=html,
                href=bs_.select_one("meta[property='og:url']")["content"],
                meta_keywords=bs_.select_one("meta[name='keywords']")["content"].split(', '),
            )
            return info
        except TypeError:
            raise ContentParsingError("some article element wasn't found")

    def request_article_info(self, slug: str) -> str:
        return self._inspector.request_get(f"{CONCRETE_ARTICLE_URL}{slug}", {}).text

    def get_folder_path(self) -> pathlib.Path:
        return self._path

    def get_name(self) -> str:
        return "binance"

    def get_inspector(self) -> RequestInspector:
        return self._inspector

