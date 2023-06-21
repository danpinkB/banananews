from typing import Any

from jinja2 import Template

from src.core.entity import ScrapperSettings, ElementRecipe, ParserType
from src.core.helper.req_inspector import RequestInspector


class HtmlScrapper:
    def __init__(self, settings: ScrapperSettings, inspector: RequestInspector = None) -> None:
        if inspector is None:
            self._inspector = RequestInspector(settings.hour_limit)
        else:
            self._inspector = inspector
        self._list_url = Template(settings.list_url)
        self._next_page_recipe = settings.next_page
        self._prev_page_recipe = settings.prev_page
        self._driver = settings.driver
        self._next_page = None
        self._prev_page = None

    def scrape_resource(self, page: Any) -> str:
        resp = self._inspector.request_get(self._list_url.render(page=page), {})
        pages = ElementRecipe(tags={"next_page": self._next_page_recipe, "prev_page": self._prev_page_recipe},
                              parser=ParserType.HTML).parse_data(resp.text)
        self._next_page, self._prev_page = pages.get("next_page"), pages.get("prev_page")
        return resp.text

    def get_next_page(self) -> str:
        return self._next_page

    def get_prev_page(self) -> str:
        return self._prev_page

    

