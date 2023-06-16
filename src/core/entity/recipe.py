from typing import NamedTuple, Optional, Any


class TagRecipe(NamedTuple):
    selector: str
    attr: Optional[str]
    filters: dict[str, dict[str:Any]]


class ElementRecipe(NamedTuple):
    tags: dict[str, TagRecipe]
    parser: str

