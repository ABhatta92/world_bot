
import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "news.db"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                article_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                perspective TEXT,
                title TEXT,
                url TEXT NOT NULL UNIQUE,
                published_at TEXT,
                summary TEXT,
                fetched_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_published_at
            ON articles(published_at)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_source
            ON articles(source)
        """)


def article_id_for(url: str) -> str:
    return hashlib.sha256(url.strip().encode("utf-8")).hexdigest()


def persist_articles(articles: list[dict]) -> int:
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    rows = []

    for article in articles:
        url = article.get("url", "").strip()
        source = article.get("source", "").strip()

        if not url or not source:
            continue

        rows.append((
            article_id_for(url),
            source,
            article.get("perspective"),
            article.get("title"),
            url,
            article.get("published_at") or None,
            article.get("summary"),
            now,
        ))

    if not rows:
        return 0

    with get_connection() as conn:
        conn.executemany("""
            INSERT INTO articles (
                article_id,
                source,
                perspective,
                title,
                url,
                published_at,
                summary,
                fetched_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                source = excluded.source,
                perspective = excluded.perspective,
                title = excluded.title,
                published_at = excluded.published_at,
                summary = excluded.summary,
                fetched_at = excluded.fetched_at
        """, rows)

    return len(rows)


def get_articles(limit: int = 50) -> list[dict]:
    if limit < 1:
        raise ValueError("limit must be positive")

    init_db()

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT *
            FROM articles
            ORDER BY fetched_at DESC
            LIMIT ?
        """, (limit,)).fetchall()

    return [dict(row) for row in rows]


def count_articles() -> int:
    init_db()

    with get_connection() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM articles"
        ).fetchone()[0]
