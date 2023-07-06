from jinja2 import Template

from src.core.entity import ReactorSettings, ArticleInfoShort
from src.core.helper.req_inspector import RequestInspector
from src.core.helper.request_driver import BaseDriver
from src.core.helper.scrapper.base_scrapper import BaseScrapper


class JsonScrapper(BaseScrapper):
    def __init__(self, settings: ReactorSettings, driver: BaseDriver, inspector: RequestInspector = None) -> None:
        if inspector is None:
            self._inspector = RequestInspector(settings.hour_limit)
        else:
            self._inspector = inspector
        self._settings = settings
        self._list_url = Template(settings.href)
        self._driver = driver

    def scrape_resource(self, page: int) -> list[ArticleInfoShort]:
        return self._settings.parse_articles(self._inspector.request_get(self._list_url.render(page=page), {}, self._driver))

