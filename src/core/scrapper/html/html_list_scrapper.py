from typing import Any

from jinja2 import Template

from src.core.entity import ScrapperSettings, ElementRecipe, ParserType, DriverType
from src.core.helper.req_inspector import RequestInspector
from src.core.helper.request_driver import BaseDriver
from src.core.scrapper.base_scrapper import BaseScrapper


class HtmlScrapper(BaseScrapper):
    def __init__(self, settings: ScrapperSettings, driver: BaseDriver, inspector: RequestInspector = None) -> None:
        if inspector is None:
            self._inspector = RequestInspector(settings.hour_limit)
        else:
            self._inspector = inspector
        self._list_url = Template(settings.href)
        self._next_page_recipe = settings.next_page
        self._prev_page_recipe = settings.prev_page
        self._driver = driver
        self._next_page = None
        self._prev_page = None

    def _parse_pages(self, resp: str) -> None:
        pages = ElementRecipe(tags={"next_page": self._next_page_recipe, "prev_page": self._prev_page_recipe},
                              parser=ParserType.HTML).parse_data(resp)
        self._next_page, self._prev_page = pages.get("next_page"), pages.get("prev_page")

    def scrape_resource(self, page: str) -> str:
        resp = self._inspector.request_get(self._list_url.render(page=page), {}, self._driver)
        self._parse_pages(resp)
        return resp

    def scrape_resource_page(self, page: str) -> str:
        resp = self._inspector.request_get_page(self._list_url, {}, self._driver, page)
        self._parse_pages(resp)
        return resp

    def get_next_page(self) -> str:
        return self._next_page

    def get_prev_page(self) -> str:
        return self._prev_page



