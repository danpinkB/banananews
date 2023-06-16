from typing import Any

from jinja2 import Template

from src.core.entity import ScrapperSettings
from src.core.helper.req_inspector import RequestInspector


class JsonScrapper:
    def __init__(self, settings: ScrapperSettings, inspector: RequestInspector = None) -> None:
        if inspector is None:
            self._inspector = RequestInspector(settings.hour_limit)
        else:
            self._inspector = inspector
        self._list_url = Template(settings.list_url)
        self._driver = settings.driver
        self._next_page = 1
        self._prev_page = 0

    def scrape_resource(self, page: Any) -> Any:
        resp = self._inspector.request_get(self._list_url.render(page=page), {})
        self._prev_page = page - 1
        self._next_page = page + 1
        return resp.json()

    def get_next_page(self) -> int:
        return self._next_page

    def get_prev_page(self) -> int:
        return self._prev_page
