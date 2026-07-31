import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "news.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,    -- хэш/уникальный ключ статьи
                url TEXT,
                title TEXT,
                published TEXT
            );
            """
        )
        conn.commit()

def seen(post_id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("SELECT 1 FROM posts WHERE id = ?", (post_id,))
        return cur.fetchone() is not None

def mark_seen(post_id: str, url: str, title: str, published: str | None):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO posts (id, url, title, published) VALUES (?,?,?,?)",
            (post_id, url, title, published),
        )
        conn.commit()
