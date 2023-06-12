from typing import Any, NamedTuple, Optional

from requests import Response

from src.resources.helper.req_inspector import RequestInspector


class ResourceArticlesSettings(NamedTuple):
    postfix: str
    args: dict[str, Any]
    changeable_arg: Optional[str]


class ScrapperSettings(NamedTuple):
    resource_url: str
    hour_limit: int
    list_setting: ResourceArticlesSettings
    concrete_setting: ResourceArticlesSettings


class Scrapper:
    def __init__(self, settings: ScrapperSettings):
        self._inspector = RequestInspector(settings.hour_limit)
        self._settings = settings
        self._resource_url = settings.resource_url
        self._hour_limit = settings.hour_limit
        self._list_setting = settings.list_setting
        self._concrete_setting = settings.concrete_setting

    def scrape_list(self, page: int):
        return self._scrape(page, "all")

    def scrape_concrete(self, arg: str) -> str:
        return self._scrape(arg, "one").text

    def _scrape(self, arg: Any, type_: str) -> Response:
        args = self._list_setting.args.copy()
        url_: str
        article_settings: ResourceArticlesSettings
        if type_ == "all":
            article_settings = self._list_setting
        elif type_ == "one":
            article_settings = self._concrete_setting
        if article_settings.changeable_arg is None:
            url_ = f'{self._resource_url}{article_settings.postfix}{arg}'
        else:
            url_ = f'{self._resource_url}{article_settings.postfix}'
            args[self._concrete_setting.changeable_arg] = arg
        print(url_, args)
        response: Response = self._inspector.request_get(url_, args)
        return response
