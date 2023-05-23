import json
import pathlib
import tempfile
import threading
import time
import zipfile
from datetime import datetime
from typing import Optional, List, Set, Dict

import requests
import sqlite3
from bs4 import BeautifulSoup
from requests import Response

ARTICLES_REQ_URL = "https://www.binance.com/bapi/composite/v1/public/cms/news/queryFlashNewsList"
CONCRETE_ARTICLE_URL = "https://www.binance.com/en/news/flash/"


class SqlliteConnector:
    conn: sqlite3.Connection
    cursor: sqlite3.Cursor

    def __init__(self):
        self.conn = sqlite3.connect("./articles.db")
        self.cursor = self.conn.cursor()
        self.conn.execute('''
        create table if not exists articles (id INTEGER PRIMARY KEY)
        ''')

    def insert_article(self, article: int):
        self.cursor.execute("insert into articles (id) values (?)", (article,))
        self.conn.commit()

    def is_parsed(self, article: int):
        self.conn.execute("select * from articles where id = ?", (article,))
        row = self.cursor.fetchone()
        return row is not None


class RequestInspector:
    lock: threading.Lock
    hour_limit: int
    minute_limit: int
    delta: int
    last_parsed_time: float
    headers: dict

    def __init__(self, hour_limit=720000, headers: dict = None):
        if headers is None:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'}
        self.hour_limit = hour_limit
        self.last_parsed_time = time.time()
        self.lock = threading.Lock()
        self.minute_limit = int(hour_limit / 60)
        self.delta = 0
        self.headers = headers

    def req(self, url: str, params: Dict) -> Response:
        with self.lock:
            self.delta += 1
            now = time.time()
            time_delta = 60 - (now - self.last_parsed_time)
            if time_delta < 60:
                if self.delta >= self.minute_limit:
                    time.sleep(time_delta)
                    self.last_parsed_time = now + time_delta
                    self.delta = 0
            else:
                self.last_parsed_time = now
                self.delta = 0
            return requests.get(url, params=params, headers=self.headers)


class RequestIterator:
    index: int
    articles: List
    prev_size: int
    page: int
    inspector: RequestInspector

    def __init__(self, inspector: RequestInspector):
        self.index = 0
        self.inspector = inspector
        self.page = 1
        self.prev_size = 20
        self.articles = list()

    def __iter__(self):
        return self

    def __next__(self):
        if self.index == len(self.articles) and self.prev_size == 20:
            resp = self.inspector.req(ARTICLES_REQ_URL,
                                      {"pageNo": self.page, "pageSize": 20, "isTransform": "false", "tagId": ""})
            self.page += 1
            if resp.status_code < 400:
                new_articles_data = resp.json().get("data").get("contents")
                self.articles.extend(new_articles_data)
                self.prev_size = len(new_articles_data)
        if self.index < len(self.articles):
            value = self.articles[self.index]
            self.index += 1
            return value
        else:
            raise StopIteration


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
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%dT%H:%M:%S%z')
        return super().default(obj)


def get_all_articles_binance(from_dt: Optional[datetime], to_dt: Optional[datetime], inspector: RequestInspector) -> \
        Set[int]:
    if from_dt is None:
        from_dt = datetime.now()
    if to_dt is None:
        to_dt = datetime(1970, 1, 1, 1)
    articles = set()
    from_: int = int(from_dt.timestamp() * 1000)
    to_: int = int(to_dt.timestamp() * 1000)
    for i in RequestIterator(inspector):
        create_time: int = i.get("createTime")
        if create_time > from_:
            continue
        if create_time < to_:
            break
        articles.add(i.get('id'))
    return articles


def get_article_info(href: str, inspector: RequestInspector) -> str:
    res = inspector.req(href, {})
    if res.status_code >= 400:
        raise RequestError(f"error while getting resource with status code - {res.status_code}")
    return res.text


def parse_article_binance(html: str) -> ArticleInfo:
    bs_ = BeautifulSoup(html, "html.parser")
    try:
        article = bs_.select_one("article.css-17l2a77")
        info = ArticleInfo()
        info.header = article.select_one("h1.css-ps28d1").text
        info.publication_dt = datetime.strptime(article.select_one("div.css-1hmgk20").text, "%Y-%m-%d %H:%M")
        info.content = article.select_one("div.css-13uwx4b").text
        info.parsing_dt = datetime.now()
        info.html = html
        info.href = bs_.select_one("meta[property='og:url']")["content"]
        info.meta_keywords = bs_.select_one("meta[name='keywords']")["content"].split(', ')
        return info
    except TypeError as err:
        raise ContentParsingError("some article element wasn't found")


def save_to_disk(file_name: str, article: ArticleInfo) -> None:
    path = pathlib.Path(f'./uploads/binance/{file_name}.zip')
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=True) as json_file, \
            tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=True) as html_file, \
            zipfile.ZipFile(path, 'w') as zipf:
        html_file.write(article.html)
        article_json = json.dumps(article.__dict__, cls=ArticleEncoder)
        json_file.write(article_json)
        zipf.write(json_file.name, f'{file_name}.json')
        zipf.write(html_file.name, f'{file_name}.html')
    return


def parse_articles(from_dt: Optional[datetime], to_dt: Optional[datetime]) -> None:
    inspector: RequestInspector = RequestInspector()
    conn = SqlliteConnector()
    for article in get_all_articles_binance(from_dt, to_dt, inspector):
        filename = f"binance_{article}"
        if not conn.is_parsed(article):
            try:
                article_html = get_article_info(f"{CONCRETE_ARTICLE_URL}{article}", inspector)
                article_info = parse_article_binance(article_html)
                save_to_disk(filename, article_info)
                conn.insert_article(article)
            except Exception as ex:
                print(ex)


if __name__ == "__main__":
    parse_articles(datetime(2023, 5, 21, 1, 0, 0), datetime(2023, 5, 20, 0, 0, 0))
