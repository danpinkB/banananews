import argparse
import importlib.util

import json
import multiprocessing
import os
import pathlib
import tempfile
import zipfile
from datetime import datetime
from functools import partial
from typing import Optional, Iterator, List

from dateutil.parser import parse

from src.const import INDEX_DB_FILE, DATA_FOLDER
from src.core.entity import ArticleInfoShort, ArticleInfo, ReactorSettings
from src.core.error import RequestError
from src.core.helper.reactor import Reactor
from src.core.helper.sqllite_connector import SqlliteConnector
import glob


def get_first_index_of_element_from_to(from_: float, to_: float, arr: list[ArticleInfoShort]) -> int:
    for i, row in enumerate(arr):
        if to_ <= row.timestamp <= from_:
            return i
    return -1


def get_all_articles_binary_search(
        from_dt: Optional[datetime],
        to_dt: Optional[datetime],
        reactor: Reactor
) -> Iterator[ArticleInfoShort]:
    if from_dt is None:
        from_dt = datetime.now()
    if to_dt is None:
        to_dt = datetime(1970, 1, 1, 1)
    from_: float = from_dt.timestamp()
    to_: float = to_dt.timestamp()

    low = 0
    high = 1000
    mid: int = 1
    articles_data = reactor.go_to_link(str(mid))

    parsed_pages = set()
    first_matched_index = get_first_index_of_element_from_to(from_, to_, articles_data)
    height_multiplier = 2
    while first_matched_index == -1:
        mid = (high + low) // 2
        if mid in parsed_pages:
            raise RequestError('date out of possible range')
        else:
            parsed_pages.add(mid)
        articles_data = reactor.go_to_link(str(mid))
        if articles_data is None or len(articles_data) == 0:
            high = mid
            height_multiplier = 1
            continue
        first_matched_index = get_first_index_of_element_from_to(from_, to_, articles_data)
        create_time: float = articles_data[first_matched_index].timestamp if first_matched_index != -1 else \
        articles_data[0].timestamp
        high, low = (high * height_multiplier, mid) if create_time > from_ else (mid, low)
    reactor.get_pager().set_pages(mid)
    while first_matched_index == 0 and mid > 1:
        mid -= 1
        prev_articles = reactor.go_to_link(str(mid))
        first_matched_index = get_first_index_of_element_from_to(from_, to_, prev_articles)
        articles_data = prev_articles + articles_data
    for article in RequestIterator(reactor, articles_data[:first_matched_index or 0]):
        # if create_time > from_:
        #     continue
        if article.timestamp < to_:
            break
        yield article


def get_all_articles(
        from_dt: Optional[datetime],
        to_dt: Optional[datetime],
        reactor: Reactor
) -> Iterator[ArticleInfoShort]:
    if from_dt is None:
        from_dt = datetime.now()
    if to_dt is None:
        to_dt = datetime(1970, 1, 1, 1)
    from_: float = from_dt.timestamp()
    to_: float = to_dt.timestamp()
    articles_data = reactor.go_to_link('1', True)
    for article in RequestIterator(reactor, articles_data):
        if article.timestamp > from_:
            continue
        if article.timestamp < to_:
            break
        yield article


def json_serial(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()


def save_to_disk(file_name: str, folder: pathlib.Path, article: ArticleInfo) -> None:
    with tempfile.TemporaryDirectory() as temp_dir, zipfile.ZipFile(folder.joinpath(f"{file_name}.zip"), 'w') as zipf:
        with open(f"{temp_dir}/{file_name}.html", 'w') as html_file:
            html_file.write(article.html)
            zipf.write(html_file.name, f'{file_name}.html')
        with open(f"{temp_dir}/{file_name}.json", 'w') as json_file:
            article_json = json.dumps(article, default=json_serial)
            json_file.write(article_json)
            zipf.write(json_file.name, f'{file_name}.json')


class RequestIterator:
    def __init__(self, reactor: Reactor, articles=None) -> None:
        if articles is None:
            articles = list()
        else:
            articles = articles
        self.index = 0
        self._reactor = reactor
        self.articles = articles

    def __iter__(self) -> Iterator[ArticleInfoShort]:
        for i in self.articles:
            if self.index == len(self.articles):
                self.articles.extend(self._reactor.page_next())
            if self.index == len(self.articles):
                raise StopIteration()
            yield i


def reactor_parse_resource(settings: ReactorSettings, from_dt: datetime, to_dt: datetime) -> List[ArticleInfo]:
    reactor = Reactor(settings)
    res = list()
    for article in get_all_articles_binary_search(from_dt, to_dt, reactor) if settings.is_binary_search else get_all_articles(from_dt, to_dt, reactor):
        res.append(reactor.article_page(article.href))
    return res


def parse_articles(
    from_dt: Optional[datetime],
    to_dt: Optional[datetime],
    settings: List[ReactorSettings],
    ignore_exist: bool,
    ignore_list_collecting: bool
) -> None:
    conn = SqlliteConnector(INDEX_DB_FILE)
    with conn, multiprocessing.Pool() as pool:
        for articles in pool.map(partial(reactor_parse_resource, from_dt=from_dt, to_dt=to_dt), settings):
            for article in articles:
                if not conn.has_article(article.id):
                    filename = f"binance_{article.id}"
                    save_to_disk(filename, DATA_FOLDER, article)
                    # conn.insert_article(ArticleRow(id = article.id, datetime.fromtimestamp(article.timestamp), ), soft=True)


def import_class_from_path(module_path, class_name):
    spec = importlib.util.spec_from_file_location("module_name", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Get the desired class from the module
    desired_class = getattr(module, class_name)
    return desired_class


if __name__ == "__main__":
    pattern = r"https://(.*?)/"
    resources = [import_class_from_path(resource, "settings") for resource in glob.glob(f"{os.getcwd()}/src/resources/*.py")]
    print(resources)
    parser = argparse.ArgumentParser()
    parser.add_argument("hrefs", type=str, nargs="+")
    parser.add_argument("--from-dt", type=lambda x: parse(x))
    parser.add_argument("--to-dt", type=lambda x: parse(x))
    parser.add_argument("--ignore-exist", type=int, default=0)
    parser.add_argument("--ignore-list-collecting", type=int, default=0)
    args = parser.parse_args()
    print(args)
    parse_articles(args.from_dt, args.to_dt, resources, args.ignore_exist, args.ignore_list_collecting)
