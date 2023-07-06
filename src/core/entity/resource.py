from typing import NamedTuple
from src.core.helper.scrapper.base_scrapper import BaseScrapper
from src.core.helper.scrapper import HtmlPageScrapper


class Resource(NamedTuple):
    scrapper: BaseScrapper
    page_scrapper: HtmlPageScrapper
    is_binary_search: bool
    is_pageble: bool

