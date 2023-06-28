from enum import Enum
from typing import NamedTuple, Optional
from .parse_resource_recipe import TagRecipe


class DriverType(Enum):
    SELENIUM = 1
    REQUEST = 2


class ScrapperSettings(NamedTuple):
    hour_limit: int
    href: str
    next_page: TagRecipe
    prev_page: TagRecipe
    list_driver: Optional[DriverType]
    page_driver: Optional[DriverType]

