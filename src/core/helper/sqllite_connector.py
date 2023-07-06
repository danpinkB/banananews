import pathlib
import sqlite3
from typing import Dict, List, Set

from src.core.entity import ArticleRow


class SqlliteConnector:
    def __init__(self, file_name: pathlib.Path):
        self._conn = sqlite3.connect(file_name)
        self._cursor = self._conn.cursor()
        self._conn.execute('''
        CREATE TABLE IF NOT EXISTS article_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            href VARCHAR(3000)
        );
        ''')
        self._conn.execute('''
        CREATE TABLE IF NOT EXISTS article_links (
            id VARCHAR(100),
            href VARCHAR(1000),
            slug VARCHAR(255),
            published_dt DATE, 
            article_resource_id INTEGER,
            parsed_dt DATE,
            article_archive_file_version INTEGER,
            article_archive_file_path VARCHAR(1000),
            FOREIGN KEY (article_resource_id) REFERENCES article_resources(id)
        );
        ''')
        self._articles: Dict[str, ArticleRow] = dict()

        self._not_saved_new: List[ArticleRow] = list()
        self._not_saved_parsed: Set[str] = set()

    # for context manager
    def __enter__(self) -> 'SqlliteConnector':
        self._cursor.execute(f"SELECT * FROM article_links ORDER BY published_dt")
        for row in self._cursor.fetchall():
            id_ = row[0]
            self._articles[id_] = ArticleRow.from_row(row)
        return self

    def __exit__(self, type_, value, traceback):
        self.save()
        self._conn.commit()

    # for context manager

    def _add_article(self, article: ArticleRow) -> None:
        self._cursor.execute("""
        INSERT INTO article_links (
            id,
            href,
            slug,
            published_dt, 
            article_resource_id,
            parsed_dt,
            article_archive_file_version,
            article_archive_file_path
        )""", article.to_row())

    def _mark_article_as_parsed(self, parsed_dt: str, article_archive_file_path: str, article_id: str) -> None:
        self._cursor.execute(f"UPDATE articles SET parsed_dt = ?, article_archive_file_version = 1, article_archive_file_path=?  WHERE id = ?", (article_id, parsed_dt, article_archive_file_path))

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

    # def set_parsed(self, article_id: str, *, soft: bool = False) -> None:
    #     if self._articles[article_id].parsed_dt is not None:
    #         return
    #     row = self._articles[article_id]
    #     self._articles[article_id] = row
    #     if soft:
    #         self._not_saved_parsed.add(article_id)
    #     else:
    #         self._mark_article_as_parsed(article_id)

    def is_parsed(self, article_id: str) -> bool:
        return self._articles.get(article_id).parsed_dt is not None

    def get_size(self) -> int:
        return len(self._articles)

    def has_article(self, article_id: str) -> bool:
        return self._articles.get(article_id, None) is not None

    def get_article_info(self, article_id: str) -> ArticleRow:
        return self._articles[article_id]
