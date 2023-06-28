import argparse
import json
import pathlib
import tempfile
import zipfile
from datetime import datetime
from typing import Optional, Iterator, Any, Generator
from src.core.error import ContentParsingError
from src.const import INDEX_DB_FILE, DATA_FOLDER
from src.core.entity import ArticleInfoShort, ArticleInfo, Resource, ElementRecipe
from src.core.error import RequestError
from src.resources import resources
from src.core.helper.sqllite_connector import SqlliteConnector
from src.core.scrapper.html.html_page_scrupper import HtmlPageScrapper
from dateutil.parser import parse


def get_first_index_of_element_from_to(from_: float, to_: float, arr: list[ArticleInfoShort]) -> int:
    for i, row in enumerate(arr):
        if to_ <= row.timestamp <= from_:
            return i
    return -1


def get_all_articles_binary_search(
        from_dt: Optional[datetime],
        to_dt: Optional[datetime],
        resource: Resource
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
    articles_data = parse_news_list(resource.scrapper.scrape_resource(mid), resource.list_recipe, resource.article_short_info_recipe)

    parsed_pages = set()
    first_matched_index = get_first_index_of_element_from_to(from_, to_, articles_data)
    height_multiplier = 2
    while first_matched_index == -1:
        mid = (high + low) // 2
        if mid in parsed_pages:
            raise RequestError('date out of possible range')
        else:
            parsed_pages.add(mid)
        articles_data = parse_news_list(resource.scrapper.scrape_resource(mid), resource.list_recipe, resource.article_short_info_recipe)
        if articles_data is None or len(articles_data) == 0:
            high = mid
            height_multiplier = 1
            continue
        first_matched_index = get_first_index_of_element_from_to(from_, to_, articles_data)
        create_time: float = articles_data[first_matched_index].timestamp if first_matched_index != -1 else \
        articles_data[0].timestamp
        high, low = (high * height_multiplier, mid) if create_time > from_ else (mid, low)
    while first_matched_index == 0 and mid > 1:
        mid -= 1
        prev_articles = parse_news_list(resource.scrapper.scrape_resource(mid), resource.list_recipe, resource.article_short_info_recipe)
        first_matched_index = get_first_index_of_element_from_to(from_, to_, prev_articles)
        articles_data = prev_articles + articles_data
    for article in RequestIterator(resource, articles_data[:first_matched_index or 0]):
        # if create_time > from_:
        #     continue
        if article.timestamp < to_:
            break
        yield article


def get_all_articles(
        from_dt: Optional[datetime],
        to_dt: Optional[datetime],
        resource: Resource
) -> Iterator[ArticleInfoShort]:
    if from_dt is None:
        from_dt = datetime.now()
    if to_dt is None:
        to_dt = datetime(1970, 1, 1, 1)
    from_: float = from_dt.timestamp()
    to_: float = to_dt.timestamp()
    articles_data = parse_news_list(resource.scrapper.scrape_resource('1'), resource.list_recipe, resource.article_short_info_recipe)
    for article in RequestIterator(resource, articles_data):
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


def parse_news_list(html: str, list_recipe: ElementRecipe, article_short_info_recipe:ElementRecipe) -> list[ArticleInfoShort]:
    parsed_articles_html = list_recipe.parse_data(html)
    articles = list()
    for article_html in parsed_articles_html.get("articles"):
        parsed_article = article_short_info_recipe.parse_data(article_html)
        articles.append(ArticleInfoShort(
            id=parsed_article.get("id"),
            href=parsed_article.get("href"),
            timestamp=parsed_article.get("datetime").timestamp()
        ))
    return articles


def parse_article(href: str, page_scrapper: HtmlPageScrapper, article_info_recipe: ElementRecipe) -> ArticleInfo:
    html = page_scrapper.scrape_resource(href)
    try:
        parsed_article = article_info_recipe.parse_data(html)
        return ArticleInfo(
            href=parsed_article.get("href"),
            parsing_dt=datetime.now(),
            content=parsed_article.get("content"),
            header=parsed_article.get("header"),
            publication_dt=parsed_article.get("publication_dt"),
            meta_keywords=parsed_article.get("meta_keywords"),
            html=html
        )
    except KeyError:
        raise ContentParsingError(f"an error while parsing article href - {href}")


class RequestIterator:
    def __init__(self, resource: Resource, articles=None) -> None:
        if articles is None:
            articles = list()
        else:
            articles = articles
        self.index = 0
        self._resource = resource
        self.articles = articles

    def __iter__(self) -> Iterator[ArticleInfoShort]:
        for i in self.articles:
            if self.index == len(self.articles):
                new_articles_data = parse_news_list(
                    self._resource.scrapper.scrape_resource_page(self._resource.scrapper.get_next_page()),
                    self._resource.list_recipe,
                    self._resource.article_short_info_recipe
                )
                self.articles.extend(new_articles_data)
            if self.index == len(self.articles):
                raise StopIteration()
            yield i


def parse_articles(
    from_dt: Optional[datetime],
    to_dt: Optional[datetime],
    resource: Resource,
    ignore_exist: bool,
    ignore_list_collecting: bool
) -> None:
    conn = SqlliteConnector(INDEX_DB_FILE)
    with conn:
        for article in get_all_articles_binary_search(from_dt, to_dt, resource) if resource.is_binary_search else get_all_articles(from_dt, to_dt, resource):
            if not conn.has_article(article.id):
                filename = f"binance_{article.id}"
                article_info = parse_article(article.href, resource.page_scrapper, resource.article_info_recipe)
                save_to_disk(filename, DATA_FOLDER, article_info)
                # conn.insert_article(ArticleRow(id = article.id, datetime.fromtimestamp(article.timestamp), ), soft=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("hrefs", type=str, nargs="+")
    parser.add_argument("--from-dt", type=lambda x: parse(x))
    parser.add_argument("--to-dt", type=lambda x: parse(x))
    parser.add_argument("--ignore-exist", type=bool, default=False)
    parser.add_argument("--ignore-list-collecting", type=bool, default=False)
    args = parser.parse_args()
    print(args)
    parse_articles(args.from_dt, args.to_dt, resources[0])
