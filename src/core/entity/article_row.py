from datetime import datetime
from typing import NamedTuple, Tuple


class ArticleRow(NamedTuple):
    id: str
    href: str
    slug: str
    published_dt: datetime
    article_resource_id: int
    parsed_dt: datetime
    article_archive_file_version: int
    article_archive_file_path: str

    @staticmethod
    def from_row(row: Tuple[str, str, str, str, int, str, int, str]) -> 'ArticleRow':
        return ArticleRow(
            id=row[0],
            href=row[1],
            slug=row[2],
            published_dt=datetime.fromisoformat(row[3]),
            article_resource_id=row[4],
            parsed_dt=datetime.fromisoformat(row[5]),
            article_archive_file_version=row[6],
            article_archive_file_path=row[7]
        )

    def to_row(self) -> Tuple[str, str, str, int, str, int, str]:
        return self.href, self.slug, self.published_dt.isoformat(), self.article_resource_id, self.parsed_dt.isoformat(), self.article_archive_file_version, self.article_archive_file_path
