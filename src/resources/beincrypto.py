from src.core.entity import ScrapperSettings, ElementRecipe, TagRecipe, ParserType, \
    DriverType, Resource
from src.core.helper.req_inspector import RequestInspector
from src.core.helper.request_driver import RequestDriver
from src.core.scrapper import HtmlScrapper, HtmlPageScrapper

settings = ScrapperSettings(
    hour_limit=720000,
    href="https://beincrypto.com/news/page/{{page}}/",
    next_page=TagRecipe(selector="a[aria-label='Next page']", attr="href", filters=["get_first"]),
    prev_page=TagRecipe(
        selector="a[aria-label='Previous page']",
        attr="href",
        filters=["get_first"]
    ),
    list_driver=DriverType.REQUEST,
    page_driver=DriverType.REQUEST
)
inspector = RequestInspector()
scrapper = HtmlScrapper(settings, RequestDriver(inspector.get_headers()), inspector)
page_scrapper = HtmlPageScrapper(settings, RequestDriver(inspector.get_headers()), inspector)

list_recipe = ElementRecipe(
    tags={"articles": TagRecipe(selector="div.card", attr=None, filters=[])},
    parser=ParserType.HTML)

article_info_recipe = ElementRecipe(
    tags={
        "header": TagRecipe(selector="article > h1.h4", attr="text", filters=["get_first"]),
        "content": TagRecipe(selector="article > div.entry-content", attr="text", filters=["get_first"]),
        "publication_dt": TagRecipe(selector="article > time", attr="datetime",
                                    filters=["get_first", "date_format_known"]),
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

beincrypto = Resource(
    list_recipe=list_recipe,
    article_short_info_recipe=article_short_info_recipe,
    article_info_recipe=article_info_recipe,
    scrapper=scrapper,
    page_scrapper=page_scrapper,
    is_binary_search=True,
    is_pageble=True
)
