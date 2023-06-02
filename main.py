import json
import os
import pathlib
import tempfile
import zipfile
from datetime import datetime
from typing import Optional, Generator

from entity.entities import ArticleInfoShort, ArticleInfo, ArticleRow
from error.errors import RequestError
from helper.req_inspector import RequestInspector
from helper.req_iterator import RequestIterator
from helper.sqllite_connector import SqlliteConnector
from parser.base_parser import Parser
from parser.potato_parser import PotatoParser

INDEX_DB_FILE = pathlib.Path(os.getcwd()) / "articles.db"


def get_first_index_of_element_from_to(from_: float, to_: float, arr: list[ArticleInfoShort]) -> int:
    for i, row in enumerate(arr):
        if to_ <= row.timestamp <= from_:
            return i
    return -1


def get_all_articles(from_dt: Optional[datetime], to_dt: Optional[datetime], inspector: RequestInspector, parser: Parser) -> \
        Generator[ArticleInfoShort, None, None]:
    if from_dt is None:
        from_dt = datetime.now()
    if to_dt is None:
        to_dt = datetime(1970, 1, 1, 1)
    from_: float = from_dt.timestamp()
    to_: float = to_dt.timestamp()

    low = 0
    high = 1000
    mid: int = 1
    articles_data: list[ArticleInfoShort] = parser.request_articles(mid)
    parsed_pages = set()
    first_matched_index = get_first_index_of_element_from_to(from_, to_, articles_data)
    height_multiplier = 2
    while first_matched_index == -1:
        mid = (high + low) // 2
        print(mid)
        if mid in parsed_pages:
            raise RequestError('date out of possible range')
        else:
            parsed_pages.add(mid)
        articles_data = parser.request_articles(mid)
        if articles_data is None or len(articles_data) == 0:
            high = mid
            height_multiplier = 1
            continue
        print(articles_data)
        first_matched_index = get_first_index_of_element_from_to(from_, to_, articles_data)
        create_time: float = articles_data[first_matched_index].timestamp if first_matched_index != -1 else articles_data[0].timestamp
        print(create_time, from_)
        high, low = (high * height_multiplier, mid) if create_time > from_ else (mid, low)
    while first_matched_index == 0 and mid > 1:
        mid -= 1
        prev_articles = parser.request_articles(mid)
        first_matched_index = get_first_index_of_element_from_to(from_, to_, prev_articles)
        articles_data = prev_articles + articles_data
    for article in RequestIterator(inspector, articles_data[:first_matched_index or 0], mid + 1):
        # if create_time > from_:
        #     continue
        if article.timestamp < to_:
            break
        yield article


def serialize_datetime(o):
    if isinstance(o, datetime):
        return o.isoformat()


def save_to_disk(file_name: str, folder: pathlib.Path, article: ArticleInfo) -> None:
    with tempfile.TemporaryDirectory() as temp_dir, zipfile.ZipFile(folder.joinpath(f"{file_name}.zip"), 'w') as zipf:
        with open(f"{temp_dir}/{file_name}.html", 'w') as html_file:
            html_file.write(article.html)
            zipf.write(html_file.name, f'{file_name}.html')
        with open(f"{temp_dir}/{file_name}.json", 'w') as json_file:
            article_json = json.dumps(article)
            json_file.write(article_json)
            zipf.write(json_file.name, f'{file_name}.json')


def parse_articles(from_dt: Optional[datetime], to_dt: Optional[datetime], parsers: list[Parser]) -> None:
    inspector: RequestInspector = RequestInspector()

    for parser in parsers:
        conn = SqlliteConnector(INDEX_DB_FILE, parser.get_name())
        with conn:
            for article in get_all_articles(from_dt, to_dt, inspector, parser):
                if not conn.has_article(article.id):
                    filename = f"binance_{article.id}"
                    article_html = parser.request_article_info(article.id)
                    article_info = parser.parse_article_info(article_html)
                    save_to_disk(filename, parser.get_folder_path(), article_info)
                    conn.insert_article(ArticleRow(article.id, datetime.fromtimestamp(article.timestamp), True), soft=True)


if __name__ == "__main__":
    parse_articles(datetime(2023, 5, 21, 1, 0, 0), datetime(2023, 5, 20, 0, 0, 0), [PotatoParser(RequestInspector()),])
