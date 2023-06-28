import re
from typing import Any, Optional

from bs4 import Tag
from datetime import datetime
from dateutil.parser import parse


def pattern_matcher(s: str, pattern_: str) -> str:
    match = re.search(pattern_, s)
    if match:
        return match.group(1)
    return ""


def get_slug_from_url(url_: str) -> str:
    return re.search(r"/([^/]+)/?$", url_).group(1)


def join_list(list_: list[str]) -> str:
    return ",".join(list_)


def parse_date_(data_: str) -> datetime:
    return parse(data_)


def date_format_known(date_: str) -> datetime:
    return parse(date_)


def date_format_b_d_Y_comma_H_M(date_: str) -> datetime:
    return datetime.strptime(date_, "%b %d, %Y,%H:%M")


def date_format_b_d_Y_A_H_M(date_: str) -> datetime:
    return datetime.strptime(date_, "%b %d, %Y @ %H:%M")


def select_prev_li_without_classes(tag: Tag) -> Optional[Tag]:
    return tag.findPrevious("li:not([class*='.'])")


def get_tag_attr(tag: Tag, attr: str) -> Any:
    match attr:
        case None:
            return str(tag)
        case "text":
            return tag.text
        case _:
            return tag[attr]


def get_tag_href(tag: Tag) -> str:
    return get_tag_attr(tag, "href") if tag is not None else ""


def split_string_dash_1(s_: str) -> str:
    return s_.split("-")[1]


functions = {
    "get_slug_from_url": get_slug_from_url,
    "join_list": join_list,
    "to_str": lambda x: str(x),
    "list_to_str": lambda arr: [str(i) for i in arr],
    "to_int": lambda x: int(x),
    "get_20_last": lambda x: x[len(x)-20:len(x)],
    "select_prev_li_without_classes": select_prev_li_without_classes,
    "get_tag_href": get_tag_href,
    "date_format_b_d_Y_comma_H_M": date_format_b_d_Y_comma_H_M,
    "date_format_b_d_Y_A_H_M": date_format_b_d_Y_A_H_M,
    "date_format_known": date_format_known,
    "split_string_dash_1": split_string_dash_1,
    "get_tag_attr": get_tag_attr,
    "get_first": lambda arr: arr[0]
}
