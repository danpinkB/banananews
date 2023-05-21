import collections.abc as collections
import json
import logging
import os.path
import threading
import time
from datetime import datetime
from typing import Optional, List

import requests
from bs4 import BeautifulSoup
from requests import Response

articles_req_url = "https://www.binance.com/bapi/composite/v1/public/cms/news/queryFlashNewsList"
concrete_article_url = "https://www.binance.com/en/news/flash/"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'}


class RequestObserver:
    lock = threading.Lock()
    hour_limit: int = 720000
    minute_limit: int = 12000
    delta: int = 0
    last_parsed_date: float = datetime.now().timestamp()

    @classmethod
    def set_hour_limit(cls, hour_limit: int) -> None:
        cls.lock.acquire()
        cls.hour_limit = hour_limit
        cls.minute_limit = int(hour_limit / 60)
        cls.lock.release()

    @classmethod
    def req(cls, f, *args, **kwargs) -> Response:
        cls.lock.acquire()
        cls.delta += 1
        now = datetime.now()
        delta = 60-now.timestamp()-cls.last_parsed_date
        if delta < 60:
            if cls.delta >= cls.minute_limit:
                time.sleep(60-now.timestamp()-cls.last_parsed_date)
                cls.delta = 0
                cls.last_parsed_date = datetime.now().timestamp()
        else:
            cls.delta = 0
            cls.last_parsed_date = datetime.now().timestamp()
        cls.lock.release()
        return f(*args, **kwargs)


class RequestError(Exception):
    pass


class ContentParsingError(Exception):
    pass


class ArticleInfo:
    header: str
    content: str
    publication_dt: datetime
    parsing_dt: datetime
    html: str
    href: str
    meta_keywords: List[str]


class ArticleEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ArticleInfo):
            return {"header": obj.header, "content": obj.content,
                    "publication_dt": obj.publication_dt.strftime('%Y-%m-%dT%H:%M:%S%z'),
                    "parsing_dt": obj.parsing_dt.strftime('%Y-%m-%dT%H:%M:%S%z'), "html": obj.html, "href": obj.href,
                    "meta_keywords": obj.meta_keywords}

        return super().default(obj)


def get_all_articles_binance(from_dt: Optional[datetime], to_dt: Optional[datetime]) -> collections.Set[str]:
    articles = set()
    if from_dt < to_dt:
        return articles
    page = 1
    resp = RequestObserver.req(requests.request, "GET", articles_req_url,
                               params={"pageNo": page, "pageSize": 20, "isTransform": "false", "tagId": ""})
    from_: float = from_dt.timestamp()
    to_: float = to_dt.timestamp()
    while True:
        if resp.status_code > 299:
            logging.log(msg="an error")
            return articles
        articles_data: List = resp.json().get("data").get("contents")
        for i in articles_data:
            create_time: float = i.get("createTime") / 1000
            if create_time > from_:
                continue
            if create_time < to_:
                return articles
            articles.add(i.get('id'))
        if len(articles_data) < 20:
            break
        page += 1
        resp = RequestObserver.req(requests.request, "GET", articles_req_url,
                                   params={"pageNo": page, "pageSize": 20, "isTransform": "false", "tagId": ""},
                                   headers=headers)
    return articles


def get_article_info(href: str) -> str:
    res = RequestObserver.req(requests.get, href, headers=headers)
    if res.status_code > 299:
        raise RequestError(f"error while getting resource with status code - {res.status_code}")
    return res.text


def parse_article_binance(html: str) -> ArticleInfo:
    bs_ = BeautifulSoup(html, "html.parser")
    try:
        article = bs_.find("article", {"class": "css-17l2a77"})
        info = ArticleInfo()
        info.header = article.find("h1", {"class": "css-ps28d1"}).text
        info.publication_dt = datetime.strptime(article.find("div", {"class": "css-1hmgk20"}).text, "%Y-%m-%d %H:%M")
        info.content = article.find("div", {"class": "css-13uwx4b"}).text
        info.parsing_dt = datetime.now()
        info.html = html
        info.href = bs_.find("meta", {"property": "og:url"})["content"]
        info.meta_keywords = bs_.find("meta", {"name": "keywords"})["content"].split(', ')
    except TypeError as err:
        raise ContentParsingError("some article element wasn't found")
    return info


def save_to_disk(file_name: str, article: ArticleInfo) -> None:
    with open(f"{file_name}.html", "w") as html_file, open(f"{file_name}.json", "w") as json_file:
        html_file.write(article.html)
        article_json = json.dumps(article, cls=ArticleEncoder)
        json_file.write(article_json)
    return


def parse_articles(from_dt: Optional[datetime], to_dt: Optional[datetime], requests_per_hour: int = 720000) -> None:
    RequestObserver.set_hour_limit(requests_per_hour)
    for article in get_all_articles_binance(from_dt, to_dt):
        filename = f"./uploads/binance/binance_{article}"
        if not os.path.exists(filename+".html"):
            try:
                article_html = get_article_info(f"https://www.binance.com/en/news/flash/{article}")
                save_to_disk(filename, parse_article_binance(article_html))
            except Exception as ex:
                logging.info(str(ex))


if __name__ == "__main__":
    parse_articles(datetime(2023, 5, 21, 1, 0, 0), datetime(2023, 5, 20, 0, 0, 0))
