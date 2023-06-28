from datetime import datetime

from src.core.entity import ScrapperSettings, ElementRecipe, TagRecipe, ArticleInfoShort, ArticleInfo, ParserType, \
    DriverType, Resource
from src.core.helper.req_inspector import RequestInspector
from src.core.helper.request_driver import RequestDriver
from src.core.scrapper import HtmlScrapper, HtmlPageScrapper


settings = ScrapperSettings(
        hour_limit=720000,
        href="https://cryptopotato.com/category/crypto-news/page/{{page}}/",
        next_page=TagRecipe(selector="ul.pagination li.active + li a", attr="href", filters=["get_first"]),
        prev_page=TagRecipe(
            selector="ul.pagination li.active",
            attr="tag",
            filters=[
                "get_first",
                "select_prev_li_without_classes",
                "get_tag_href"
            ]),
        list_driver=DriverType.REQUEST,
        page_driver=DriverType.REQUEST
    )
inspector = RequestInspector()
scrapper = HtmlScrapper(settings, RequestDriver(inspector.get_headers()), inspector)
page_scrapper = HtmlPageScrapper(settings,RequestDriver(inspector.get_headers()), inspector)


list_recipe = ElementRecipe(
    tags={"articles": TagRecipe(selector="article", attr=None, filters=[])},
    parser=ParserType.HTML)

article_info_recipe = ElementRecipe(
    tags={
        "header": TagRecipe(selector="div.entry-post > header > div.page-title > h1", attr="text", filters=["get_first"]),
        "content": TagRecipe(selector="div.entry-post > div", attr="text", filters=["get_first"]),
        "publication_dt": TagRecipe(selector="div.entry-post > header > div.entry-meta > span.entry-date > span", attr="text", filters=["get_first", "date_format_b_d_Y_A_H_M"]),
        "href": TagRecipe(selector="head > meta[property='og:url']", attr="content", filters=["get_first"]),
        "meta_keywords": TagRecipe(selector="meta[content]", attr="content", filters=[])
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

potato = Resource(
    list_recipe=list_recipe,
    article_short_info_recipe=article_short_info_recipe,
    article_info_recipe=article_info_recipe,
    scrapper=scrapper,
    page_scrapper=page_scrapper,
    is_binary_search=True,
    is_pageble=True
)

