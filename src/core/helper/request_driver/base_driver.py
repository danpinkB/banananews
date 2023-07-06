from typing import Dict

from jinja2 import Template


class BaseDriver:

    def get_resource(self, url: str, req_args: Dict[str, str]) -> str:
        pass