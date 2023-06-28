from datetime import datetime
from typing import NamedTuple, Tuple


class ResourceRow(NamedTuple):
    id: int
    href: str

    @staticmethod
    def from_row(row: Tuple[int, str]) -> 'ArticleRow':
        return ResourceRow(
            id=row[0],
            href=row[1]
        )

    def to_row(self) -> Tuple[int, str]:
        return self.id, self.href
