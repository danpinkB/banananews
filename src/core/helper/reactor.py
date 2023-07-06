from datetime import datetime
from typing import Any

from jinja2 import Template

from src.core.entity import ReactorSettings, DriverType, ArticleInfoShort, PagerType, ArticleInfo
from src.core.helper.pager import BasePager, SimplePager, SelectorPager, SeleniumPager
from src.core.helper.req_inspector import RequestInspector
from src.core.helper.request_driver import RequestDriver, SeleniumDriver


class Reactor:
    def __init__(self, settings: ReactorSettings):
        self._inspector = RequestInspector(settings.hour_limit)
        self._settings = settings
        self._href = Template(settings.href)
        self._list_driver = RequestDriver(self._inspector) if settings.list_driver == DriverType.REQUEST else SeleniumDriver(self._inspector)
        self._page_driver = RequestDriver(self._inspector) if settings.list_driver == DriverType.REQUEST else SeleniumDriver(self._inspector)
        self._pager: BasePager

        if settings.pager_type == PagerType.SELECTOR:
            self._pager = SelectorPager(settings.next_page, settings.prev_page, self._list_driver)
        elif settings.pager_type == PagerType.SIMPLE:
            self._pager = SimplePager(self._list_driver, self._href)
        elif settings.pager_type == PagerType.SELENIUM:
            self._pager = SeleniumPager(settings.next_page, settings.prev_page, self._list_driver)

    def go_to_link(self, page: Any, set_pages=False) -> list[ArticleInfoShort]:
        resp = self._list_driver.get_resource(self._href.render(page=page), {})
        if set_pages:
            self._pager.set_pages(resp)
        return self._settings.parse_articles(resp)

    def get_pager(self) -> BasePager:
        return self._pager

    def article_page(self, url: str) -> ArticleInfo:
        return self._settings.parse_article(self._page_driver.get_resource(url, {}))

    def page_next(self) -> list[ArticleInfoShort]:
        return self._settings.parse_articles(self._pager.get_next())

    def page_prev(self) -> list[ArticleInfoShort]:
        return self._settings.parse_articles(self._pager.get_prev())


