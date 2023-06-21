from datetime import datetime
from typing import NamedTuple, Tuple


class ArticleRow(NamedTuple):
    id: str
    dt: datetime
    parsed: bool

    @staticmethod
    def from_row(row: Tuple[str, str, int]) -> 'ArticleRow':
        return ArticleRow(
            id=row[0],
            dt=datetime.fromisoformat(row[1]),
            parsed=bool(row[2]),
        )

    def to_row(self) -> Tuple[str, str, int]:
        return self.id, self.dt.isoformat(), int(self.parsed)
