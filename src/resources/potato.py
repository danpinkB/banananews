from datetime import datetime

from src.core.entity import ScrapperSettings, ElementRecipe, TagRecipe, ArticleInfoShort, ArticleInfo, ParserType
from src.core.helper.req_inspector import RequestInspector
from src.core.scrapper import HtmlScrapper, HtmlPageScrapper


settings = ScrapperSettings(
        hour_limit=720000,
        list_url="https://cryptopotato.com/category/crypto-news/page/{{page}}/",
        article_url="https://cryptopotato.com/?p={{id}}",
        next_page=TagRecipe(selector="ul.pagination li.active + li", attr="href", filters=["get_first"]),
        prev_page=TagRecipe(
            selector="ul.pagination li.active",
            attr="tag",
            filters=[
                "get_first",
                "select_prev_li_without_classes"
                "get_tag_href"
            ]),
        driver=""
    )
inspector = RequestInspector()
scrapper = HtmlScrapper(settings, inspector)
page_scrapper = HtmlPageScrapper(settings, inspector)


list_recipe = ElementRecipe(
    tags={"articles": TagRecipe(selector="article", attr=None, filters=[])},
    parser=ParserType.HTML)

article_info_recipe = ElementRecipe(
    tags={
        "header": TagRecipe(selector="div.entry-post > div.page-title", attr="text", filters=["get_first"]),
        "content": TagRecipe(selector="div.entry-post > div.coincodex-content", attr="text", filters=["get_first"]),
        "publication_dt": TagRecipe(selector="div.entry-post > span.last-modified-timestamp", attr="text", filters=["get_first","date_format_b_d_Y_A_H_M"]),
        "href": TagRecipe(selector="meta[property='og:url']", attr="content", filters=["get_first"]),
        "meta_keywords": TagRecipe(selector="meta", attr="content", filters=[])
    },
    parser=ParserType.HTML)

article_short_info_recipe = ElementRecipe(
    tags={
        "id": TagRecipe(
            selector="article",
            attr="id",
            filters=[
                "get_first",
                "split_string_dash_1"
            ]),
        "href": TagRecipe(
            selector="article > a",
            attr="href",
            filters=["get_first"]
        ),
        "datetime": TagRecipe(
            selector="div.entry-meta time.entry-date,span.entry-time",
            attr="text",
            filters=["join_list", "date_format_b_d_Y_comma_H_M"]
        )
    },
    parser=ParserType.HTML)


def parse_potato_list(page: int) -> list[ArticleInfoShort]:
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


def parse_potato_article(id_: int) -> ArticleInfo:
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

