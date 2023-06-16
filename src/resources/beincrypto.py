from datetime import datetime

from src.core.entity import ScrapperSettings, ElementRecipe, TagRecipe, ArticleInfoShort, ArticleInfo
from src.core.helper.req_inspector import RequestInspector
from src.core.parser.parser_ import parse_data
from src.core.scrapper import HtmlScrapper
from src.core.scrapper.html.html_scrapper import HtmlPageScrapper

settings = ScrapperSettings(
        hour_limit=720000,
        list_url="https://beincrypto.com/news/page/{{page}}/",
        article_url="https://beincrypto.com/{{id}}",
        next_page=TagRecipe(selector="a[aria-label='Next page']", attr="href", filters={"get_first": {}}),
        prev_page=TagRecipe(
            selector="a[aria-label='Previous page']",
            attr="href",
            filters={
                "get_first": {}
            }),
        driver=""
    )
inspector = RequestInspector()
scrapper = HtmlScrapper(settings, inspector)
page_scrapper = HtmlPageScrapper(settings, inspector)

list_recipe = ElementRecipe(
    tags={"articles": TagRecipe(selector="div.card", attr=None, filters={})},
    parser="html.parser")

article_info_recipe = ElementRecipe(
    tags={
        "header": TagRecipe(selector="article > h1.h4", attr="text", filters={"get_first": {}}),
        "content": TagRecipe(selector="article > div.entry-content", attr="text", filters={"get_first": {}}),
        "publication_dt": TagRecipe(selector="article > time", attr="datetime", filters={"get_first": {}, "parse_date": {"format_": "%Y-%m-%dT%H:%M:%S%z"}}),
        "href": TagRecipe(selector="meta[property='og:url']", attr="content", filters={"get_first": {}}),
        "meta_keywords": TagRecipe(selector="meta", attr="content", filters={})
    },
    parser="html.parser")

article_short_info_recipe = ElementRecipe(
    tags={
        "id": TagRecipe(
            selector="h5.h-full a",
            attr="href",
            filters={
                "get_first": {},
                "pattern_matcher": {"pattern_": r"https:\/\/beincrypto.com\/(.+?)\/"}
            }),
        "datetime": TagRecipe(
            selector="time.ago",
            attr="datetime",
            filters={
                "get_first": {},
                "parse_date": {"format_": "%Y-%m-%dT%H:%M:%S%z"}
            })
    },
    parser="html.parser")


def parse_bein_crypto_list(page: int) -> list[ArticleInfoShort]:
    html = scrapper.scrape_resource(page)
    parsed_articles_html = parse_data(html, list_recipe)
    articles = list()
    for article_html in parsed_articles_html.get("articles"):
        parsed_article = parse_data(article_html, article_short_info_recipe)
        articles.append(ArticleInfoShort(
            id=parsed_article.get("id"),
            timestamp=parsed_article.get("datetime").timestamp()
        ))
    return articles


def parse_bein_crypto_article(id_: int) -> ArticleInfo:
    html = page_scrapper.scrape_page(id_)
    parsed_article = parse_data(html, article_info_recipe)
    return ArticleInfo(
        href=parsed_article.get("href"),
        parsing_dt=datetime.now(),
        content=parsed_article.get("content"),
        header=parsed_article.get("header"),
        publication_dt=parsed_article.get("publication_dt"),
        meta_keywords=parsed_article.get("meta_keywords"),
        html=html
    )

