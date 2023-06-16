import json
from typing import Any

from bs4 import BeautifulSoup, Tag

from src.core.entity import ElementRecipe
from .functions import functions
from jsonpath_ng import parse, jsonpath


def parse_data(data: Any, recipe: ElementRecipe) -> dict[str, Any]:
    result = dict()
    match recipe.parser:
        case "html.parser":
            bs_ = BeautifulSoup(data, recipe.parser)
            for field_name in recipe.tags:
                tag = recipe.tags.get(field_name)
                selected_tags = bs_.select(tag.selector)
                if len(selected_tags) > 0:
                    result[field_name] = _call_filters_chain(tag.filters, [get_tag_attr(tag_, tag.attr) for tag_ in selected_tags])
                else:
                    result[field_name] = None
        case "json.parser":
            json_data = json.loads(data)
            for field_name in recipe.tags:
                tag = recipe.tags.get(field_name)
                jsonpath_exp = parse(tag.selector)
                result[field_name] = parse("")
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
