from enum import Enum


class ParserType(Enum):
    HTML = "html.parser"
    JSON = "json"
    RSS = "lxml"
    RSS_JSON = "rssjson"

