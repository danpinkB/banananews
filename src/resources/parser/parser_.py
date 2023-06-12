from typing import NamedTuple, Callable, Any, Optional

from bs4 import BeautifulSoup


class TagRecipe(NamedTuple):
    selector: str
    attr: Optional[str]
    filters: list[Optional[Callable]]


class ElementRecipe(NamedTuple):
    tags: dict[str, TagRecipe]
    parser: str


def parse(data: str, recipe: ElementRecipe) -> dict[str, list[Any]]:
    bs_ = BeautifulSoup(data, recipe.parser)

    result = dict()
    for i in recipe.tags:
        tag = recipe.tags.get(i)
        matches = list()
        for tag_data in bs_.select(tag.selector):
            res: Any
            match tag.attr:
                case None:
                    res = str(tag_data)
                case "text":
                    res = tag_data.text
                case _:
                    res = tag_data[tag.attr]
            matches.append(res)
        result[i] = matches
    return result

