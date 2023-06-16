from datetime import datetime

from src.core.entity import ScrapperSettings, ElementRecipe, TagRecipe, ArticleInfoShort, ArticleInfo
from src.core.parser import parse
from src.core.scrapper import HtmlScrapper

scrapper = HtmlScrapper(
    ScrapperSettings(
        hour_limit=720000,
        list_url="https://cryptopotato.com/category/crypto-news/page/{{page}}/",
        article_url="https://cryptopotato.com/?p={{id}}",
        next_page=TagRecipe(selector="ul.pagination li.active + li", attr="text", filters={"get_first": {}, "to_int": {}}),
        prev_page=TagRecipe(
            selector="ul.pagination li.active",
            attr="tag",
            filters={
                "get_first": {},
                "select_prev_tag": {"selector": "li:not([class*='.'])"},
                "get_tag_attr": {"attr": "text"},
                "to_int": {}
            }),
        driver=""
    ))

list_recipe = ElementRecipe(
    tags={"articles": TagRecipe(selector="article", attr=None, filters={})},
    parser="html.parser")

article_info_recipe = ElementRecipe(
    tags={
        "header": TagRecipe(selector="div.entry-post > div.page-title", attr="text", filters={"get_first": {}}),
        "content": TagRecipe(selector="div.entry-post > div.coincodex-content", attr="text", filters={"get_first": {}}),
        "publication_dt": TagRecipe(selector="div.entry-post > span.last-modified-timestamp", attr="text", filters={"get_first": {}, "parse_date": {"format_": "%b %d, %Y @ %H:%M"}}),
        "href": TagRecipe(selector="meta[property='og:url']", attr="content", filters={"get_first": {}}),
        "meta_keywords": TagRecipe(selector="meta",attr="content", filters={})
    },
    parser="html.parser")

article_short_info_recipe = ElementRecipe(
    tags={
        "id": TagRecipe(
            selector="article",
            attr="id",
            filters={
                "get_first": {},
                "split_string": {"delimiter": "-", "index_to_get": 1}
            }),
        "datetime": TagRecipe(
            selector="div.entry-meta time.entry-date,span.entry-time",
            attr="text",
            filters={
                "join_list": {},
                "parse_date": {"format_": "%b %d, %Y,%H:%M"}
            })
    },
    parser="html.parser")


def parse_potato_list(page: int) -> list[ArticleInfoShort]:
    html = scrapper.scrape_resource(page)
    parsed_articles_html = parse(html, list_recipe)
    articles = list()
    for article_html in parsed_articles_html.get("articles"):
        parsed_article = parse(article_html, article_short_info_recipe)
        articles.append(ArticleInfoShort(
            id=parsed_article.get("id")[0],
            timestamp=parsed_article.get("datetime").timestamp()
        ))
    return articles


def parse_article(id_: int) -> ArticleInfo:
    html = scrapper.scrape_page(id_)
    parsed_article = parse(html, article_info_recipe)
    return ArticleInfo(
        href=parsed_article.get("href"),
        parsing_dt=datetime.now(),
        content=parsed_article.get("content"),
        header=parsed_article.get("header"),
        publication_dt=parsed_article.get("publication_dt"),
        meta_keywords=parsed_article.get("meta_keywords"),
        html=html
    )

