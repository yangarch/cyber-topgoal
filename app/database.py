import sqlite3
import os
from datetime import datetime
from typing import List
from .models import Comment, CommentCreate

DB_PATH = os.environ.get("DATA_DIR", "/data") + "/comments.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def create_comment(comment: CommentCreate):
    conn = get_db_connection()
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    c.execute(
        'INSERT INTO comments (nickname, content, created_at) VALUES (?, ?, ?)',
        (comment.nickname, comment.content, created_at)
    )
    conn.commit()
    comment_id = c.lastrowid
    conn.close()
    return Comment(id=comment_id, nickname=comment.nickname, content=comment.content, created_at=created_at)

def get_comments() -> List[Comment]:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM comments ORDER BY created_at DESC')
    rows = c.fetchall()
    comments = []
    for row in rows:
        comments.append(Comment(**dict(row)))
    conn.close()
    return comments
