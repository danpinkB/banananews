from typing import NamedTuple
from .parse_resource_recipe import TagRecipe


class ScrapperSettings(NamedTuple):
    hour_limit: int
    list_url: str
    article_url: str
    next_page: TagRecipe
    prev_page: TagRecipe
    driver: str

