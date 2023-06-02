import pathlib
import sqlite3
from typing import Dict, List, Set

from entity.entities import ArticleRow


class SqlliteConnector:
    def __init__(self, file_name: pathlib.Path, table_name: str = "articles"):
        self._conn = sqlite3.connect(file_name)
        self._cursor = self._conn.cursor()
        self._table_name = f"{table_name}_articles"
        self._conn.execute('''
        CREATE TABLE IF NOT EXISTS '''+self._table_name+''' (
            id VARCHAR(36) PRIMARY KEY, 
            posted_date DATE, 
            is_parsed INTEGER
        )
        ''')
        self._articles: Dict[str, ArticleRow] = dict()
        self._cursor.execute(f"SELECT * FROM {self._table_name} ORDER BY posted_date")
        for row in self._cursor.fetchall():
            id_ = row[0]
            self._articles[id_] = ArticleRow.from_row(row)

        self._not_saved_new: List[ArticleRow] = list()
        self._not_saved_parsed: Set[str] = set()

    # for context manager
    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.save()
        self._conn.commit()

    # for context manager

    def _add_article(self, article: ArticleRow) -> None:
        self._cursor.execute(f"INSERT INTO {self._table_name} (id, posted_date, is_parsed) VALUES (?, ?, ?)", article.to_row())

    def _mark_article_as_parsed(self, article_id: str) -> None:
        self._cursor.execute(f"UPDATE {self._table_name} SET is_parsed = 1 WHERE id = ?", (article_id,))

    def save(self) -> None:
        for article in self._not_saved_new:
            self._add_article(article)
        self._not_saved_new.clear()

        for article_id in self._not_saved_parsed:
            self._mark_article_as_parsed(article_id)
        self._not_saved_parsed.clear()

    def insert_article(self, article: ArticleRow, *, soft: bool = False) -> None:
        if article.id in self._articles:
            return

        self._articles[article.id] = article

        if soft:
            self._not_saved_new.append(article)
        else:
            self._add_article(article)

    def set_parsed(self, article_id: str, *, soft: bool = False) -> None:
        if self._articles[article_id].parsed:
            return

        self._articles[article_id] = ArticleRow(
            id=self._articles[article_id].id,
            dt=self._articles[article_id].dt,
            parsed=True,
        )
        if soft:
            self._not_saved_parsed.add(article_id)
        else:
            self._mark_article_as_parsed(article_id)

    def is_parsed(self, article_id: str) -> bool:
        return self._articles.get(article_id).parsed

    def get_size(self) -> int:
        return len(self._articles)

    def has_article(self, article_id: str) -> bool:
        return self._articles.get(article_id, None) is not None

    def get_article_info(self, article_id: str) -> ArticleRow:
        return self._articles[article_id]
