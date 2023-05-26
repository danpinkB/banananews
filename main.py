import collections
import json
import pathlib
import tempfile
import threading
import time
import zipfile
from datetime import datetime
from typing import Optional, Set, Dict, Tuple

import requests
import sqlite3
from bs4 import BeautifulSoup
from requests import Response

ARTICLES_REQ_URL = "https://www.binance.com/bapi/composite/v1/public/cms/news/queryFlashNewsList"
CONCRETE_ARTICLE_URL = "https://www.binance.com/en/news/flash/"


class SqlliteConnector:
    def __init__(self):
        self.conn = sqlite3.connect("./articles.db")
        self.cursor = self.conn.cursor()
        self.conn.execute('''
        create table if not exists articles (
            id INTEGER PRIMARY KEY, 
            posted_date DATE, 
            is_parsed INTEGER
        )
        ''')
        self.articles = dict()
        self.articles_ids = list()
        self.cursor.execute("select * from articles order by posted_date")
        for row in self.cursor.fetchall():
            id_ = row[0]
            self.articles[id_] = (datetime.strptime(row[1], "%Y-%m-%dT%H:%M:%S"), row[2])
            self.articles_ids.append(id_)

    # for context manager
    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.conn.commit()

    # for context manager

    def insert_article(self, article: int, posted_date: datetime, is_parsed: int)->None:
        self.cursor.execute("insert into articles (id,posted_date,is_parsed) values (?,?,?)",
                            (article, posted_date.isoformat(), is_parsed))
        self.articles[article] = (posted_date, is_parsed)
        self.articles_ids.insert(0, article)

    def set_parsed(self, article: int) -> None:
        self.cursor.execute("update articles set is_parsed = 1 where id = ?", (article,))

    def is_parsed(self, article: int) -> bool:
        return self.articles.get(article)[1] == 1

    def get_size(self) -> int:
        return len(self.articles_ids)

    def has_article(self, article: int) -> bool:
        return self.articles.get(article) is not None

    def __getitem__(self, item) -> int:
        return self.articles_ids[item]

    def get_article_info(self, article: int) -> Tuple:
        return self.articles.get(article)


class RequestInspector:
    def __init__(self, req_hour_rate=720000, headers: Dict = None):
        if headers is None:
            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'}
        self.hour_limit = req_hour_rate
        self.last_parsed_time = time.time()
        self.lock = threading.Lock()
        self.minute_rate = int(req_hour_rate / 60)
        self.delta = 0
        self.headers = headers

    def request_get(self, url: str, req_args: Dict) -> Response:
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
    def __init__(self, inspector: RequestInspector):
        self.index = 0
        self.inspector = inspector
        self.page = 1
        self.prev_size = 200
        self.articles = list()

    def __iter__(self) -> Dict:
        for i in self.articles:
            if self.index == len(self.articles) and self.prev_size == 200:
                resp = self.inspector.request_get(ARTICLES_REQ_URL,
                                                  {"pageNo": self.page, "pageSize": 200, "isTransform": "false",
                                                   "tagId": ""})
                self.page += 1
                new_articles_data = resp.json().get("data").get("contents")
                self.articles.extend(new_articles_data)
                self.prev_size = len(new_articles_data)
            yield i
            self.index += 1

    def __next__(self) -> Dict:
        pass


class RequestError(Exception):
    pass


class ContentParsingError(Exception):
    pass


ArticleInfo = collections.namedtuple('ArticleInfo', ['header', 'content', 'publication_dt',
                                                     'parsing_dt', 'html', 'href', 'meta_keywords'])
ArticleInfoShort = collections.namedtuple('ArticleInfo', ['id', 'createTime'])


# class CustomEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, datetime):
#             return obj.isoformat()
#         return super().default(obj)


def get_all_articles_binance(from_dt: Optional[datetime], to_dt: Optional[datetime], inspector: RequestInspector) -> \
        Set[ArticleInfoShort]:
    if from_dt is None:
        from_dt = datetime.now()
    if to_dt is None:
        to_dt = datetime(1970, 1, 1, 1)
    articles = set()
    from_: int = int(from_dt.timestamp() * 1000)
    to_: int = int(to_dt.timestamp() * 1000)
    for article in RequestIterator(inspector):
        create_time: int = article.get("createTime")
        if create_time > from_:
            continue
        if create_time < to_:
            break
        articles.add(ArticleInfoShort(article.get("id"), article.get("createTime") / 1000))
    return articles


# def get_article_info(href: str, inspector: RequestInspector) -> str:
#     return inspector.request_get(href, {}).text


def parse_article_binance(html: str) -> ArticleInfo:
    bs_ = BeautifulSoup(html, "html.parser")
    try:
        article = bs_.select_one("article.css-17l2a77")
        header = article.select_one("h1.css-ps28d1").text
        publication_dt = datetime.strptime(article.select_one("div.css-1hmgk20").text, "%Y-%m-%d %H:%M").isoformat()
        content = article.select_one("div.css-13uwx4b").text
        parsing_dt = datetime.now().isoformat()
        href = bs_.select_one("meta[property='og:url']")["content"]
        meta_keywords = bs_.select_one("meta[name='keywords']")["content"].split(', ')
        info = ArticleInfo(header, content, publication_dt, parsing_dt, html, href, meta_keywords)
        return info
    except TypeError:
        raise ContentParsingError("some article element wasn't found")


def save_to_disk(file_name: str, article: ArticleInfo) -> None:
    path = pathlib.Path(f'./uploads/binance')
    with tempfile.TemporaryDirectory() as temp_dir, \
            zipfile.ZipFile(path.joinpath(f"{file_name}.zip"), 'w') as zipf:
        with open(f"{temp_dir}/{file_name}.html", 'w') as html_file:
            html_file.write(article.html)
            zipf.write(html_file.name, f'{file_name}.html')
        with open(f"{temp_dir}/{file_name}.json", 'w') as json_file:
            article_json = json.dumps(article)
            json_file.write(article_json)
            zipf.write(json_file.name, f'{file_name}.json')
    return


def find_index(conn: SqlliteConnector, from_dt: Optional[datetime], to_dt: Optional[datetime]) -> int:
    end = conn.get_size() - 1
    size_ = conn.get_size()
    start = 0
    while True:
        middle = end - int((end - start) / 2)
        if middle == size_:
            return middle
        index_date: datetime = conn.get_article_info(conn[middle])[0]
        prev_date: datetime = conn.get_article_info(conn[middle + 1])[0]
        if middle == 0:
            return 0
        if to_dt <= index_date <= from_dt < prev_date:
            return middle
        if index_date < from_dt:
            start = middle
            continue
        if index_date > to_dt:
            end = middle
            continue


def parse_articles(from_dt: Optional[datetime], to_dt: Optional[datetime]) -> None:
    inspector: RequestInspector = RequestInspector()
    conn = SqlliteConnector()
    with conn:
        for article in get_all_articles_binance(None, None, inspector):
            if not conn.has_article(article.id):
                conn.insert_article(article.id, datetime.fromtimestamp(article.createTime), 0)
            else:
                break
    index: int = find_index(conn, from_dt, to_dt)
    if index != -1:
        with conn:
            for i in range(index):
                article_id: int = conn[index - i]
                if conn.get_article_info(article_id)[0] < to_dt:
                    break
                if conn.is_parsed(article_id):
                    continue
                filename = f"binance_{article_id}"
                try:
                    article_html = inspector.request_get(f"{CONCRETE_ARTICLE_URL}{article_id}", {}).text
                    article_info = parse_article_binance(article_html)
                    save_to_disk(filename, article_info)
                    conn.set_parsed(article_id)
                except Exception as ex:
                    print(ex)


if __name__ == "__main__":
    parse_articles(datetime(2023, 5, 21, 1, 0, 0), datetime(2023, 5, 20, 0, 0, 0))
