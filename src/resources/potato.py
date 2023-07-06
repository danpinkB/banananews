from src.core.entity import ReactorSettings, ElementRecipe, TagRecipe, ParserType, \
    DriverType, Resource, PagerType
list_recipe = ElementRecipe(
    tags={"articles": TagRecipe(selector="article", attr=None, filters=[], action=None)},
    parser=ParserType.HTML)

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
            selector="article",
            attr="id",
            filters=[
                "get_first",
                "split_string_dash_1"
            ],
            action=None),
        "href": TagRecipe(
            selector="article > a",
            attr="href",
            filters=["get_first"],
            action=None
        ),
        "datetime": TagRecipe(
            selector="div.entry-meta time.entry-date,span.entry-time",
            attr="text",
            filters=["join_list", "date_format_b_d_Y_comma_H_M"],
            action=None
        )
    },
    parser=ParserType.HTML)

settings = ReactorSettings(
        hour_limit=720000,
        href="https://cryptopotato.com/category/crypto-news/page/{{page}}/",
        # next_page=TagRecipe(selector="ul.pagination li.active + li a", attr="href", filters=["get_first"], action=None),
        # prev_page=TagRecipe(
        #     selector="ul.pagination li.active",
        #     attr="tag",
        #     filters=[
        #         "get_first",
        #         "select_prev_li_without_classes",
        #         "get_tag_href"
        #     ],
        #     action=None),
        next_page=None,
        prev_page=None,
        list_driver=DriverType.REQUEST,
        page_driver=DriverType.REQUEST,
        pager_type=PagerType.SIMPLE,
        list_recipe=list_recipe,
        article_info_recipe=article_info_recipe,
        article_short_info_recipe=article_short_info_recipe,
        is_binary_search=True
    )




