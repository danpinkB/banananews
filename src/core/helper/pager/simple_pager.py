from jinja2 import Template

from src.core.helper.request_driver import RequestDriver
from .base_pager import BasePager


class SimplePager(BasePager):
    def __init__(self, driver: RequestDriver, href: Template):
        self._driver = driver
        self._href = href
        self._next_page = None
        self._prev_page = None

    def set_pages(self, page: int) -> None:
        self._next_page, self._prev_page = page + 1, page - 1

    def get_next(self) -> str:
        res = self._driver.get_resource(self._href.render(page=self._next_page), {})
        self.set_pages(self._next_page)
        return res

    def get_prev(self) -> str:
        res = self._driver.get_resource(self._href.render(self._prev_page), {})
        self.set_pages(self._prev_page)
        return res
