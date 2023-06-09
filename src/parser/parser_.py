from typing import NamedTuple, Callable, Any

from bs4 import BeautifulSoup


class TagRecipe(NamedTuple):
    tag: str
    attr: str
    filters: [Callable]


class ElementRecipe(NamedTuple):
    tags: dict[str, str]
    parser: str


def parse(data: str, recipe: ElementRecipe) -> dict[str, list[str]]:
    bs_ = BeautifulSoup(data, recipe.parser)
    result = dict()
    for i in recipe.tags:
        tag = recipe.tags.get(i)
        result[i] = [str(i) for i in bs_.select(tag)]
    return result

