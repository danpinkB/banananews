from typing import Any

from jinja2 import Template
from selenium.webdriver.common.by import By

from src.core.entity import TagRecipe
from src.core.helper.request_driver import SeleniumDriver
from .base_pager import BasePager


class SeleniumPager(BasePager):
    def __init__(self, next_page: TagRecipe, prev_page: TagRecipe, driver: SeleniumDriver):
        self._driver = driver
        self._next_page_recipe = next_page
        self._prev_page_recipe = prev_page

    def set_pages(self, page: Any) -> None:
        pass

    def get_next(self) -> str:
        self._driver.move_to_page(self._next_page_recipe.attr, self._next_page_recipe.selector, self._next_page_recipe.action)
        return self._driver.get_data()

    def get_prev(self) -> str:
        self._driver.move_to_page(self._prev_page_recipe.attr, self._prev_page_recipe.selector, self._prev_page_recipe.action)
        return self._driver.get_data()
