from typing import Any

from jinja2 import Template

from src.core.entity import ScrapperSettings
from src.core.helper.req_inspector import RequestInspector


class JsonPageScrapper:
    def __init__(self, settings: ScrapperSettings, inspector: RequestInspector = None) -> None:
        if inspector is None:
            self._inspector = RequestInspector(settings.hour_limit)
        else:
            self._inspector = inspector
        self._article_url = Template(settings.article_url)
        self._driver = settings.driver

    def scrape_resource(self, id_: Any) -> Any:
        return self._inspector.request_get(self._article_url.render(id=id_), {}).json()

