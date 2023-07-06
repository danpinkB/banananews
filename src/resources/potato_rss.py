from src.core.entity import ReactorSettings, ElementRecipe, TagRecipe, ParserType, \
    DriverType, PagerType

list_recipe = ElementRecipe(
    tags={"articles": TagRecipe(selector="entries", attr="tag", filters=[], action=None)},
    parser=ParserType.RSS)

article_info_recipe = ElementRecipe(
    tags={
        "id": TagRecipe(selector="article", attr="id", filters=["get_first", "split_string_dash_1"], action=None),
        "header": TagRecipe(selector="div.entry-post > header > div.page-title > h1", attr="text", filters=["get_first"], action=None),
        "content": TagRecipe(selector="div.entry-post > div", attr="text", filters=["get_first"], action=None),
        "slug": TagRecipe(selector="head > meta[property='og:url']", attr="content", filters=["get_slug_from_url"], action=None),
        "publication_dt": TagRecipe(selector="div.entry-post > header > div.entry-meta > span.entry-date > span", attr="text", filters=["get_first", "date_format_b_d_Y_A_H_M"], action=None),
        "href": TagRecipe(selector="head > meta[property='og:url']", attr="content", filters=["get_first"], action=None),
        "meta_keywords": TagRecipe(selector="meta[content]", attr="content", filters=[], action=None)
    },
    parser=ParserType.HTML)


article_short_info_recipe = ElementRecipe(
    tags={
        "id": TagRecipe(
            selector="link",
            attr=None,
            filters=[
                "get_slug_from_url"
            ],
            action=None),
        "href": TagRecipe(
            selector="link",
            attr=None,
            filters=[],
            action=None
        ),
        "datetime": TagRecipe(
            selector="published",
            attr=None,
            filters=["date_format_known"],
            action=None
        )
    },
    parser=ParserType.RSS_JSON)


settings = ReactorSettings(
        hour_limit=720000,
        href="https://cryptopotato.com/feed/",
        next_page=None,
        prev_page=None,
        list_driver=DriverType.REQUEST,
        page_driver=DriverType.REQUEST,
        list_recipe=list_recipe,
        article_info_recipe=article_info_recipe,
        article_short_info_recipe=article_short_info_recipe,
        pager_type=PagerType.NONE,
        is_binary_search=False
    )


