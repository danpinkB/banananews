from src.core.entity import ElementRecipe, ParserType, TagRecipe
from src.core.helper.request_driver import RequestDriver
from .base_pager import BasePager


class SelectorPager(BasePager):
    def __init__(self, next_page: TagRecipe, prev_page: TagRecipe, driver: RequestDriver):
        self._next_page_recipe = next_page
        self._prev_page_recipe = prev_page
        self._driver = driver
        self._next_page = None
        self._prev_page = None

    def set_pages(self, html: str) -> None:
        pages = ElementRecipe(tags={"next_page": self._next_page_recipe, "prev_page": self._prev_page_recipe},
                              parser=ParserType.HTML).parse_data(html)
        self._next_page, self._prev_page = pages.get("next_page"), pages.get("prev_page")

    def get_next(self) -> str:
        res = self._driver.get_resource(self._next_page, {})
        self.set_pages(res)
        return res

    def get_prev(self) -> str:
        res = self._driver.get_resource(self._prev_page, {})
        self.set_pages(res)
        return res
