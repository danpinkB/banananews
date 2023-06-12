import json
import os
import pathlib
import tempfile
import zipfile
from datetime import datetime
from typing import Optional, Iterator

from src.core.entity.entities import ArticleInfoShort, ArticleInfo
from src.core.error import RequestError
from src.resources.helper.req_iterator import RequestIterator
from src.resources.helper.sqllite_connector import SqlliteConnector
from src.resources.parser import parse
from src.resources.parser.parser_ import ElementRecipe, TagRecipe
from src.resources.scrapper import Scrapper, ScrapperSettings, ResourceArticlesSettings

INDEX_DB_FILE = pathlib.Path(os.getcwd()) / "articles.db"


def get_first_index_of_element_from_to(from_: float, to_: float, arr: list[ArticleInfoShort]) -> int:
    for i, row in enumerate(arr):
        if to_ <= row.timestamp <= from_:
            return i
    return -1


def get_articles(scrapper: Scrapper,
                 list_recipe: ElementRecipe,
                 concrete_recipe: ElementRecipe,
                 mid: int):
    parsed_articles = parse(scrapper.scrape_list(mid).text, list_recipe)
    parsed_data = [parse(i, concrete_recipe) for i in parsed_articles['articles']]
    articles_data: list[ArticleInfoShort] = [ArticleInfoShort(id=i.get("id")[0], timestamp=i.get("timestamp")[0]) for i
                                             in parsed_data]
    return articles_data


def get_all_articles(
        from_dt: Optional[datetime],
        to_dt: Optional[datetime],
        scrapper: Scrapper,
        list_recipe: ElementRecipe,
        concrete_recipe: ElementRecipe) -> \
        Iterator[ArticleInfoShort]:
    if from_dt is None:
        from_dt = datetime.now()
    if to_dt is None:
        to_dt = datetime(1970, 1, 1, 1)
    from_: float = from_dt.timestamp()
    to_: float = to_dt.timestamp()

    low = 0
    high = 1000
    mid: int = 1
    articles_data = get_articles(scrapper, list_recipe, concrete_recipe, mid)
    return None
    parsed_pages = set()
    first_matched_index = get_first_index_of_element_from_to(from_, to_, articles_data)
    height_multiplier = 2
    while first_matched_index == -1:
        mid = (high + low) // 2
        if mid in parsed_pages:
            raise RequestError('date out of possible range')
        else:
            parsed_pages.add(mid)
        articles_data = get_articles(scrapper, list_recipe, concrete_recipe, mid)
        if articles_data is None or len(articles_data) == 0:
            high = mid
            height_multiplier = 1
            continue
        first_matched_index = get_first_index_of_element_from_to(from_, to_, articles_data)
        create_time: float = articles_data[first_matched_index].timestamp if first_matched_index != -1 else articles_data[0].timestamp
        high, low = (high * height_multiplier, mid) if create_time > from_ else (mid, low)
    while first_matched_index == 0 and mid > 1:
        mid -= 1
        prev_articles = get_articles(scrapper, list_recipe, concrete_recipe, mid)
        first_matched_index = get_first_index_of_element_from_to(from_, to_, prev_articles)
        articles_data = prev_articles + articles_data
    for article in RequestIterator(scrapper, articles_data[:first_matched_index or 0], mid + 1):
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


def parse_articles(from_dt: Optional[datetime], to_dt: Optional[datetime]) -> None:
    scrapper: Scrapper = Scrapper(ScrapperSettings(resource_url="https://cryptopotato.com/",
                                                   hour_limit=720000,
                                                   list_setting=ResourceArticlesSettings(
                                                       postfix="category/crypto-news/page/",
                                                       changeable_arg=None,
                                                       args={}
                                                   ),
                                                   concrete_setting=ResourceArticlesSettings(
                                                       postfix="",
                                                       changeable_arg="p",
                                                       args={}
                                                   ),
                                                   ))

    conn = SqlliteConnector(INDEX_DB_FILE)
    all_recipe = ElementRecipe(tags={
        "articles": TagRecipe(selector="article", attr=None, filters=[])
        },
        parser="html.parser")
    # concrete_recipe = ElementRecipe(tags={
    #     "header": TagRecipe(selector="div.entry-post > div.page-title", attr="text", filters=[]),
    #     "content": TagRecipe(selector="div.entry-post > div.coincodex-content", attr="text", filters=[]),
    #     "publication_dt": TagRecipe(selector="div.entry-post > span.last-modified-timestamp", attr="text", filters=[]),
    #     "href": TagRecipe(selector="meta[property='og:url']", attr="content", filters=[]),
    #     "meta_keywords": TagRecipe(selector="meta", attr="content", filters=[])
    #     },
    #     parser="html.parser")
    concrete_recipe = ElementRecipe(tags={
        "id": TagRecipe(selector="article", attr="id", filters=[]),
        "datetime": TagRecipe(selector="time", attr="datetime", filters=[]),
        "time": TagRecipe(selector="span.entry-time", attr="text", filters=[])
        },
        parser="html.parser")
    with conn:
        for article in get_all_articles(from_dt, to_dt, scrapper, all_recipe, concrete_recipe):
            if not conn.has_article(article.id):
                filename = f"binance_{article.id}"
                # article_html = parser.request_article_info(article.id)
                # article_info = parser.parse_article_info(article_html)
                # save_to_disk(filename, parser.get_folder_path(), article_info)
                # conn.insert_article(ArticleRow(article.id, datetime.fromtimestamp(article.timestamp), True), soft=True)


if __name__ == "__main__":
    parse_articles(datetime(2023, 5, 21, 1, 0, 0), datetime(2023, 5, 20, 0, 0, 0))
