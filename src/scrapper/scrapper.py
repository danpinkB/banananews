from typing import Any, Callable, Optional, NamedTuple

from requests import Response
from src.helper.req_inspector import RequestInspector


class ScrapperSettings(NamedTuple):
    resource_url: str
    hour_limit: int
    get_all_articles_postfix: str
    get_concrete_article_postfix: str
    get_all_args: dict
    get_concrete_args: dict
    page_arg: str



class Scrapper:
    def __init__(self, settings: ScrapperSettings):
        self.__inspector = RequestInspector(settings.hour_limit)
        self.__settings = settings

    def scrape_list(self, page: int):
        self.__settings.get_all_args[self.__settings.page_arg] = page
        response: Response = self.__inspector.request_get(f'{self.__settings.resource_url}{self.__settings.get_all_articles_postfix}', self.__settings.get_all_args)
        return response

    def scrape_concrete(self) -> str:
        response: Response = self.__inspector.request_get(f'{self.__settings.resource_url}{self.__settings.get_concrete_article_postfix}', self.__settings.get_concrete_args)
        return response.text
