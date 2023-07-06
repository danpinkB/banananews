from typing import Dict

import requests

from src.core.error import RequestError
from src.core.helper.req_inspector import RequestInspector
from src.core.helper.request_driver.base_driver import BaseDriver


class RequestDriver(BaseDriver):
    def __init__(self, inspector: RequestInspector) -> None:
        self._headers = inspector.get_headers()
        self._inspector = inspector

    def get_resource(self, url: str, req_args: Dict[str, str]) -> str:
        self._inspector.lock_request()
        res = requests.get(url, params=req_args, headers=self._headers)
        if res.status_code >= 400:
            raise RequestError(f"error while getting resource with status code - {res.status_code}")
        return res.text
