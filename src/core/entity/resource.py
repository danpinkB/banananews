from typing import NamedTuple
from .parse_resource_recipe import ElementRecipe
from ..scrapper.base_scrapper import BaseScrapper
from ..scrapper.html.html_page_scrupper import HtmlPageScrapper


class Resource(NamedTuple):
    list_recipe: ElementRecipe
    article_short_info_recipe: ElementRecipe
    article_info_recipe: ElementRecipe
    scrapper: BaseScrapper
    page_scrapper: HtmlPageScrapper
    is_binary_search: bool
    is_pageble: bool

