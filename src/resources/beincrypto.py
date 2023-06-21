from datetime import datetime

from src.core.entity import ScrapperSettings, ElementRecipe, TagRecipe, ArticleInfoShort, ArticleInfo, ParserType
from src.core.helper.req_inspector import RequestInspector
from src.core.scrapper import HtmlScrapper, HtmlPageScrapper

settings = ScrapperSettings(
        hour_limit=720000,
        list_url="https://beincrypto.com/news/page/{{page}}/",
        article_url="https://beincrypto.com/{{id}}",
        next_page=TagRecipe(selector="a[aria-label='Next page']", attr="href", filters=["get_first"]),
        prev_page=TagRecipe(
            selector="a[aria-label='Previous page']",
            attr="href",
            filters=["get_first"]
            ),
        driver=""
    )
inspector = RequestInspector()
scrapper = HtmlScrapper(settings, inspector)
page_scrapper = HtmlPageScrapper(settings, inspector)

list_recipe = ElementRecipe(
    tags={"articles": TagRecipe(selector="div.card", attr=None, filters=[])},
    parser=ParserType.HTML)

article_info_recipe = ElementRecipe(
    tags={
        "header": TagRecipe(selector="article > h1.h4", attr="text", filters=["get_first"]),
        "content": TagRecipe(selector="article > div.entry-content", attr="text", filters=["get_first"]),
        "publication_dt": TagRecipe(selector="article > time", attr="datetime", filters=["get_first", "date_format_known"]),
        "href": TagRecipe(selector="meta[property='og:url']", attr="content", filters=["get_first"]),
        "meta_keywords": TagRecipe(selector="meta", attr="content", filters=[])
    },
    parser=ParserType.HTML)

article_short_info_recipe = ElementRecipe(
    tags={
        "id": TagRecipe(
            selector="h5.h-full a",
            attr="href",
            filters=["get_first", "get_slug_from_url"]),
        "href": TagRecipe(
            selector="figure > a",
            attr="href",
            filters=["get_first"]
        ),
        "datetime": TagRecipe(
            selector="time.ago",
            attr="datetime",
            filters=["get_first", "date_format_known"]
        )
    },
    parser=ParserType.HTML)


def parse_bein_crypto_list(page: int) -> list[ArticleInfoShort]:
    html = scrapper.scrape_resource(page)
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


def parse_bein_crypto_article(id_: int) -> ArticleInfo:
    html = page_scrapper.scrape_page(id_)
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

