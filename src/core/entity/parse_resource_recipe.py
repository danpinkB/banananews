import json
from typing import NamedTuple, Optional, Any
from bs4 import BeautifulSoup, Tag
from src.core.functions import functions
from jsonpath_ng import parse
from .parser_type import ParserType
import feedparser


class TagRecipe(NamedTuple):
    selector: str
    attr: Optional[str]
    action: Optional[str]
    filters: list[str]


class ElementRecipe(NamedTuple):
    tags: dict[str, TagRecipe]
    parser: ParserType

    def parse_data(self, data: Any) -> dict[str, Any]:
        result = dict()
        match self.parser:
            case ParserType.HTML:
                bs_ = BeautifulSoup(data, self.parser.value)
                for field_name in self.tags:
                    tag = self.tags.get(field_name)
                    selected_tags = bs_.select(tag.selector)
                    if len(selected_tags) > 0:
                        result[field_name] = _call_filters_chain(tag.filters, [_get_tag_attr(tag_, tag.attr) for tag_ in selected_tags])
                    else:
                        result[field_name] = None
            case ParserType.JSON:
                json_data = json.loads(data)
                for field_name in self.tags:
                    tag = self.tags.get(field_name)
                    exp = parse(tag.selector)
                    result[field_name] = exp.find(json_data)
            case ParserType.RSS:
                rss = feedparser.parse(data)
                for field_name in self.tags:
                    tag = self.tags.get(field_name)
                    selected_tags = rss[tag.selector]
                    if len(selected_tags) > 0:
                        result[field_name] = _call_filters_chain(tag.filters, [_get_tag_attr(tag_, tag.attr) for tag_ in selected_tags])
                    else:
                        result[field_name] = None
            case ParserType.RSS_JSON:
                json_data = data
                for field_name in self.tags:
                    tag = self.tags.get(field_name)
                    result[field_name] = _call_filters_chain(tag.filters, json_data[tag.selector])
        return result


def _get_tag_attr(tag: Tag, attr: str) -> Any:
    match attr:
        case None:
            return str(tag)
        case "text":
            return tag.text
        case "tag":
            return tag
        case _:
            return tag[attr]


def _call_filters_chain(functions_: list, result: Any) -> Any:
    for function_name in functions_:
        result = functions[function_name](result)
    return result
