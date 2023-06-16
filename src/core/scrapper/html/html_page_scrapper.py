from typing import Any

from jinja2 import Template

from src.core.entity import ScrapperSettings
from src.core.helper.req_inspector import RequestInspector


class HtmlPageScrapper:
    def __init__(self, settings: ScrapperSettings, inspector: RequestInspector = None) -> None:
        self._article_url = Template(settings.article_url)
        self._driver = settings.driver
        if inspector is None:
            self._inspector = RequestInspector(settings.hour_limit)
        else:
            self._inspector = inspector

    def scrape_page(self, id_: Any) -> str:
        return self._inspector.request_get(self._article_url.render(id=id_), {}).text

