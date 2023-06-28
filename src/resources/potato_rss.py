from datetime import datetime

from src.core.entity import ScrapperSettings, ElementRecipe, TagRecipe, ArticleInfoShort, ArticleInfo, ParserType, \
    DriverType, Resource
from src.core.helper.req_inspector import RequestInspector
from src.core.helper.request_driver import RequestDriver
from src.core.scrapper import HtmlScrapper, HtmlPageScrapper


settings = ScrapperSettings(
        hour_limit=720000,
        href="https://cryptopotato.com/feed/",
        next_page=TagRecipe(selector="none", attr=None, filters=[]),
        prev_page=TagRecipe(selector="none", attr=None, filters=[]),
        list_driver=DriverType.REQUEST,
        page_driver=DriverType.REQUEST
    )
inspector = RequestInspector()
scrapper = HtmlScrapper(settings, RequestDriver(inspector.get_headers()), inspector)
page_scrapper = HtmlPageScrapper(settings, RequestDriver(inspector.get_headers()), inspector)

list_recipe = ElementRecipe(
    tags={"articles": TagRecipe(selector="entries", attr="tag", filters=[])},
    parser=ParserType.RSS)

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
            selector="link",
            attr=None,
            filters=[
                "get_slug_from_url"
            ]),
        "href": TagRecipe(
            selector="link",
            attr=None,
            filters=[]
        ),
        "datetime": TagRecipe(
            selector="published",
            attr=None,
            filters=["date_format_known"]
        )
    },
    parser=ParserType.RSS_JSON)


potato_rss = Resource(
    list_recipe=list_recipe,
    article_short_info_recipe=article_short_info_recipe,
    article_info_recipe=article_info_recipe,
    scrapper=scrapper,
    page_scrapper=page_scrapper,
    is_binary_search=False,
    is_pageble=True
)
