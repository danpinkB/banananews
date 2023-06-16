import re
from typing import Any

from bs4 import Tag
from datetime import datetime

pattern_ = r'(\n\w+ \d{1,2}, \d{4}\n\d{2}:\d{2})'


def data_matcher(s: str) -> str:
    match = re.search(pattern_, s)
    if match:
        return match.group()
    return ""


def join_list(list_: list[str]) -> str:
    return ",".join(list_)


def parse_date(data_: str, format_: str) -> datetime:
    return datetime.strptime(data_, format_)


def select_prev(tag: Tag, selector: str) -> Tag:
    res = tag.findPrevious(selector)
    if res is None:
        return tag
    return res


def get_tag_attr(tag: Tag, attr: str) -> Any:
    match attr:
        case None:
            return str(tag)
        case "text":
            return tag.text
        case _:
            return tag[attr]


def split_string(s_: str, delimiter: str, index_to_get: int) -> str:
    return s_.split(delimiter)[index_to_get]


functions = {
    "data_match": data_matcher,
    "join_list": join_list,
    "to_int": lambda x: int(x),
    "select_prev_tag": select_prev,
    "parse_date": parse_date,
    "split_string": split_string,
    "get_tag_attr": get_tag_attr,
    "get_first": lambda arr: arr[0]
}
