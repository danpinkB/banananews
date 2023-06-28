from typing import Dict

import requests
from jinja2 import Template

from src.core.error import RequestError
from src.core.helper.request_driver.base_driver import BaseDriver


class RequestDriver(BaseDriver):
    def __init__(self, headers: Dict[str, str]) -> None:
        self._headers = headers

    def get_resource(self, url: str, req_args: Dict[str, str]) -> str:
        res = requests.get(url, params=req_args, headers=self._headers)
        if res.status_code >= 400:
            raise RequestError(f"error while getting resource with status code - {res.status_code}")
        return res.text

    def get_page(self, url: Template, req_args: Dict[str, str], page: str) -> str:
        res = requests.get(url.render(page=page), params=req_args, headers=self._headers)
        if res.status_code >= 400:
            raise RequestError(f"error while getting resource with status code - {res.status_code}")
        return res.text
