import json
import os
import pathlib
import sqlite3
import tempfile
import threading
import time
import zipfile
from datetime import datetime
from typing import Optional, Set, Dict, Tuple, NamedTuple, Generator, Any, List

import requests
from bs4 import BeautifulSoup
from requests import Response

ARTICLES_REQ_URL = "https://www.binance.com/bapi/composite/v1/public/cms/news/queryFlashNewsList"
CONCRETE_ARTICLE_URL = "https://www.binance.com/en/news/flash/"
INDEX_DB_FILE = pathlib.Path(os.getcwd()) / "articles.db"


class ArticleRow(NamedTuple):
    id: int
    dt: datetime
    parsed: bool

    @staticmethod
    def from_row(row: Tuple[int, str, int]) -> 'ArticleRow':
        return ArticleRow(
            id=row[0],
            dt=datetime.fromisoformat(row[1]),
            parsed=bool(row[2]),
        )

    def to_row(self) -> Tuple[int, str, int]:
        return (self.id, self.dt.isoformat(), int(self.parsed))


class SqlliteConnector:
    def __init__(self, file_name: pathlib.Path):
        self._conn = sqlite3.connect(file_name)
        self._cursor = self._conn.cursor()
        self._conn.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY, 
            posted_date DATE, 
            is_parsed INTEGER
        )
        ''')
        self._articles: Dict[int, ArticleRow] = dict()
        self._cursor.execute("SELECT * FROM articles ORDER BY posted_date")
        for row in self._cursor.fetchall():
            id_ = row[0]
            self._articles[id_] = ArticleRow.from_row(row)

        self._not_saved_new: List[ArticleRow] = list()
        self._not_saved_parsed: Set[int] = set()

    # for context manager
    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.save()
        self._conn.commit()

    # for context manager

    def _add_article(self, article: ArticleRow) -> None:
        self._cursor.execute("INSERT INTO articles (id, posted_date, is_parsed) VALUES (?, ?, ?)", article.to_row())

    def _mark_article_as_parsed(self, article_id: int) -> None:
        self._cursor.execute("UPDATE articles SET is_parsed = 1 WHERE id = ?", (article_id,))

    def save(self) -> None:
        for article in self._not_saved_new:
            self._add_article(article)
        self._not_saved_new.clear()

        for article_id in self._not_saved_parsed:
            self._mark_article_as_parsed(article_id)
        self._not_saved_parsed.clear()

    def insert_article(self, article: ArticleRow, *, soft: bool = False) -> None:
        if article.id in self._articles:
            return

        self._articles[article.id] = article

        if soft:
            self._not_saved_new.append(article)
        else:
            self._add_article(article)

    def set_parsed(self, article_id: int, *, soft: bool = False) -> None:
        if self._articles[article_id].parsed:
            return

        self._articles[article_id] = ArticleRow(
            id=self._articles[article_id].id,
            dt=self._articles[article_id].dt,
            parsed=True,
        )
        if soft:
            self._not_saved_parsed.add(article_id)
        else:
            self._mark_article_as_parsed(article_id)

    def is_parsed(self, article_id: int) -> bool:
        return self._articles.get(article_id).parsed

    def get_size(self) -> int:
        return len(self._articles)

    def has_article(self, article_id: int) -> bool:
        return self._articles.get(article_id, None) is not None

    def get_article_info(self, article_id: int) -> ArticleRow:
        return self._articles[article_id]


class RequestInspector:
    def __init__(self, req_hour_rate=720000, headers: Optional[Dict[str, str]] = None) -> None:
        headers = dict((k.strip().lower(), v) for k, v in (headers or dict()).items())
        if 'user-agent' not in headers:
            headers['user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
        self.hour_limit = req_hour_rate
        self.last_parsed_time = time.time()
        self.lock = threading.Lock()
        self.minute_rate = int(req_hour_rate / 60)
        self.delta = 0
        self.headers = headers

    def request_get(self, url: str, req_args: Dict[str, str]) -> Response:
        with self.lock:
            self.delta += 1
            now = time.time()
            time_delta = 60 - (now - self.last_parsed_time)
            if time_delta < 60:
                if self.delta >= self.minute_rate:
                    time.sleep(time_delta)
                    self.last_parsed_time = now + time_delta
                    self.delta = 0
            else:
                self.last_parsed_time = now
                self.delta = 0
            res = requests.get(url, params=req_args, headers=self.headers)
            if res.status_code >= 400:
                raise RequestError(f"error while getting resource with status code - {res.status_code}")
            return res


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

    def request_articles(self) -> List[Dict[str, Any]]:
        resp = self._inspector.request_get(ARTICLES_REQ_URL,
                                           {"pageNo": self._page, "pageSize": 20, "isTransform": "false", "tagId": ""}) \
            .json().get("data").get("contents")
        self._page += 1
        return resp or list()

    def __iter__(self) -> Generator[Dict[str, Any], None, None]:
        if len(self._articles) == 0:
            self._articles.extend(self.request_articles())
        for i in self._articles:
            yield i
            self._index += 1
            if self._index == len(self._articles) - 1:
                self._articles.extend(self.request_articles())

    def __next__(self) -> None:
        pass


class RequestError(Exception):
    pass


class ContentParsingError(Exception):
    pass


class ArticleInfo(NamedTuple):
    href: str
    html: str
    header: str
    content: str
    meta_keywords: List[str]
    publication_dt: datetime
    parsing_dt: datetime


class ArticleInfoShort(NamedTuple):
    id: int
    timestamp: float

def get_condition_index(from_: int, to_: int, arr: list) -> int:
    for i in range(len(arr)):
        if to_ <= int(arr[i]['createTime']) <= from_:
            return i
    return -1


def get_all_articles_binance(from_dt: Optional[datetime], to_dt: Optional[datetime], inspector: RequestInspector) -> \
        Set[ArticleInfoShort]:
    if from_dt is None:
        from_dt = datetime.now()
    if to_dt is None:
        to_dt = datetime(1970, 1, 1, 1)
    articles = set()
    from_: int = int(from_dt.timestamp() * 1000)
    to_: int = int(to_dt.timestamp() * 1000)

    low = 0
    high = 1000
    mid: int = 1
    articles_data: list = list()
    while len(articles_data) == 0 or articles_data[0]['createTime'] >= from_:
        try:
            articles_data = inspector\
                .request_get(ARTICLES_REQ_URL, {"pageNo": mid, "pageSize": 20, "isTransform": "false", "tagId": ""}) \
                .json().get("data").get("contents")
            low = mid
            high *= 2
            mid = (high + low) // 2
        except RequestError:
            articles_data.clear()
            break

    condition_index = get_condition_index(from_, to_, articles_data)
    parsed_pages = {0}

    while condition_index == -1 or (condition_index == 0 and mid - 1 not in parsed_pages):
        mid = (high + low) // 2
        parsed_pages.add(mid)
        try:
            articles_data = inspector \
                .request_get(ARTICLES_REQ_URL, {"pageNo": mid, "pageSize": 20, "isTransform": "false", "tagId": ""}) \
                .json().get("data").get("contents")
        except RequestError:
            articles_data.clear()
        if articles_data is None or len(articles_data) == 0:
            high = mid
            continue
        condition_index = get_condition_index(from_, to_, articles_data)
        if condition_index != -1:
            create_time = articles_data[condition_index]['createTime']
        else:
            create_time = articles_data[0]['createTime']
        if create_time > from_:
            low = mid
        else:
            high = mid
    iterator = RequestIterator(inspector, articles_data[:condition_index or 0], mid+1)
    for article in iterator:
        create_time: int = article["createTime"]
        # if create_time > from_:
        #     continue
        if create_time < create_time:
            break
        articles.add(ArticleInfoShort(int(article["id"]), create_time / 1000))
    return articles


# def get_article_info(href: str, inspector: RequestInspector) -> str:
#     return inspector.request_get(href, {}).text


def parse_article_binance(html: str) -> ArticleInfo:
    bs_ = BeautifulSoup(html, "html.parser")
    try:
        article = bs_.select_one("article.css-17l2a77")
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


def save_to_disk(file_name: str, article: ArticleInfo) -> None:
    path = pathlib.Path(f'./uploads/binance')
    with tempfile.TemporaryDirectory() as temp_dir, zipfile.ZipFile(path.joinpath(f"{file_name}.zip"), 'w') as zipf:
        with open(f"{temp_dir}/{file_name}.html", 'w') as html_file:
            html_file.write(article.html)
            zipf.write(html_file.name, f'{file_name}.html')
        with open(f"{temp_dir}/{file_name}.json", 'w') as json_file:
            article_json = json.dumps(article)
            json_file.write(article_json)
            zipf.write(json_file.name, f'{file_name}.json')


def parse_articles(from_dt: Optional[datetime], to_dt: Optional[datetime]) -> None:
    inspector: RequestInspector = RequestInspector()
    conn = SqlliteConnector(INDEX_DB_FILE)

    with conn:
        for article in get_all_articles_binance(from_dt, to_dt, inspector):
            if not conn.has_article(article.id):
                filename = f"binance_{article.id}"
                article_html = inspector.request_get(f"{CONCRETE_ARTICLE_URL}{article.id}", {}).text
                article_info = parse_article_binance(article_html)
                save_to_disk(filename, article_info)
                conn.insert_article(ArticleRow(article.id, datetime.fromtimestamp(article.timestamp), True), soft=True)


if __name__ == "__main__":
    parse_articles(datetime(2023, 5, 21, 1, 0, 0), datetime(2023, 5, 20, 0, 0, 0))
