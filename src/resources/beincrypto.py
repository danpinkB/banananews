from src.core.entity import ReactorSettings, ElementRecipe, TagRecipe, ParserType, \
    DriverType, PagerType


list_recipe = ElementRecipe(
    tags={"articles": TagRecipe(selector="div.card", attr=None, filters=[], action=None)},
    parser=ParserType.HTML)

article_info_recipe = ElementRecipe(
    tags={
        "id": TagRecipe(selector="article", attr="id", filters=["get_first", "split_string_dash_1"], action=None),
        "slug": TagRecipe(selector="head > meta[property='og:url']", attr="content", filters=["get_slug_from_url"], action=None),
        "header": TagRecipe(selector="article > h1.h4", attr="text", filters=["get_first"], action=None),
        "content": TagRecipe(selector="article > div.entry-content", attr="text", filters=["get_first"], action=None),
        "publication_dt": TagRecipe(selector="article > time", attr="datetime",
                                    filters=["get_first", "date_format_known"], action=None),
        "href": TagRecipe(selector="meta[property='og:url']", attr="content", filters=["get_first"], action=None),
        "meta_keywords": TagRecipe(selector="meta[content]", attr="content", filters=[], action=None)
    },
    parser=ParserType.HTML)

article_short_info_recipe = ElementRecipe(
    tags={
        "id": TagRecipe(
            selector="h5.h-full a",
            attr="href",
            filters=["get_first", "get_slug_from_url"],
            action=None
        ),
        "href": TagRecipe(
            selector="figure > a",
            attr="href",
            filters=["get_first"],
            action=None
        ),
        "datetime": TagRecipe(
            selector="time.ago",
            attr="datetime",
            filters=["get_first", "date_format_known"],
            action=None
        )
    },
    parser=ParserType.HTML)

settings = ReactorSettings(
    hour_limit=720000,
    href="https://beincrypto.com/news/page/{{page}}/",
    next_page=TagRecipe(selector="a[aria-label='Next page']", attr="href", filters=["get_first"], action=None),
    prev_page=TagRecipe(
        selector="a[aria-label='Previous page']",
        attr="href",
        filters=["get_first"],
        action=None
    ),
    list_driver=DriverType.REQUEST,
    page_driver=DriverType.REQUEST,
    pager_type=PagerType.SIMPLE,
    list_recipe=list_recipe,
    article_info_recipe=article_info_recipe,
    article_short_info_recipe=article_short_info_recipe,
    is_binary_search=True
)

