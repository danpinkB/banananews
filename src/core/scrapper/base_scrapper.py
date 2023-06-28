from typing import Any


class BaseScrapper:
    def scrape_resource(self, page: Any) -> str:
        pass

    def scrape_resource_page(self, page: Any) -> str:
        pass

    def get_next_page(self) -> str:
        pass

    def get_prev_page(self) -> str:
        pass

