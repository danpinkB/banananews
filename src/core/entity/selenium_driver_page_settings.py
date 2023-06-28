from enum import Enum
from typing import NamedTuple

from selenium.webdriver.common.by import By


class PageGetterAction(Enum):
    CLICK = 1,
    SCROLL = 2


class PageGetterSettings(NamedTuple):
    get_by: By
    action: PageGetterAction
