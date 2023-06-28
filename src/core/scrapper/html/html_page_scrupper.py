from src.core.entity import ScrapperSettings
from src.core.helper.req_inspector import RequestInspector
from src.core.helper.request_driver import BaseDriver


class HtmlPageScrapper:
    def __init__(self, settings: ScrapperSettings, driver:BaseDriver, inspector: RequestInspector = None) -> None:

        if inspector is None:
            self._inspector = RequestInspector(settings.hour_limit)
        else:
            self._inspector = inspector
        self._driver = driver

    def scrape_resource(self, href: str) -> str:
        return self._inspector.request_get(href, {}, self._driver)

