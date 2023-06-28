from typing import Any

from jinja2 import Template

from src.core.entity import ScrapperSettings
from src.core.helper.req_inspector import RequestInspector
from src.core.helper.request_driver import BaseDriver
from src.core.scrapper.base_scrapper import BaseScrapper


class JsonScrapper(BaseScrapper):
    def __init__(self, settings: ScrapperSettings, driver: BaseDriver, inspector: RequestInspector = None) -> None:
        if inspector is None:
            self._inspector = RequestInspector(settings.hour_limit)
        else:
            self._inspector = inspector
        self._list_url = Template(settings.href)
        self._driver = driver
        self._next_page = -1
        self._prev_page = -1

    def scrape_resource(self, page: int) -> str:
        resp = self._inspector.request_get(self._list_url.render(page=page), {}, self._driver)
        self._prev_page, self._next_page = page - 1, page+1
        return resp

    def scrape_resource_page(self, page: int) -> str:
        resp = self._inspector.request_get_page(self._list_url, {}, self._driver, page)
        self._prev_page, self._next_page = page - 1, page+1
        return resp

    def get_next_page(self) -> int:
        return self._next_page

    def get_prev_page(self) -> int:
        return self._prev_page
