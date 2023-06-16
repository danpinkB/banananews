from typing import Any

from bs4 import BeautifulSoup, Tag

from src.core.entity import ElementRecipe
from .functions import functions


def parse(data: str, recipe: ElementRecipe) -> dict[str, Any]:
    bs_ = BeautifulSoup(data, recipe.parser)

    result = dict()
    for i in recipe.tags:
        tag = recipe.tags.get(i)
        result[i] = _call_filters_chain(tag.filters, [get_tag_attr(tag_, tag.attr) for tag_ in bs_.select(tag.selector)])
    return result


def get_tag_attr(tag: Tag, attr: str) -> Any:
    match attr:
        case None:
            return str(tag)
        case "text":
            return tag.text
        case "tag":
            return tag
        case _:
            return tag[attr]


def _call_filters_chain(functions_: dict, result: Any) -> Any:
    for function_name in functions_:
        result = functions[function_name](result, **functions_[function_name])
    return result
