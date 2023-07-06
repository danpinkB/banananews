from typing import Any


class BasePager:
    def set_pages(self, data: Any) -> None:
        pass

    def get_next(self) -> str:
        pass

    def get_prev(self) -> str:
        pass

