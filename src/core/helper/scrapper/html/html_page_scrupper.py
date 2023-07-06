from src.core.entity import ReactorSettings, ArticleInfo
from src.core.helper.req_inspector import RequestInspector
from src.core.helper.request_driver import BaseDriver


class HtmlPageScrapper:
    def __init__(self, settings: ReactorSettings, driver: BaseDriver, inspector: RequestInspector = None) -> None:
        self._settings = settings
        if inspector is None:
            self._inspector = RequestInspector(settings.hour_limit)
        else:
            self._inspector = inspector
        self._driver = driver

    def scrape_resource(self, href: str) -> ArticleInfo:
        return self._settings.parse_article(self._inspector.request_get(href, {}, self._driver))

