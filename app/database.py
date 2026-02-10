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
    c.execute('''
        CREATE TABLE IF NOT EXISTS track_stats (
            file_id TEXT PRIMARY KEY,
            play_count INTEGER DEFAULT 0,
            finish_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def increment_play_count(file_id: str):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO track_stats (file_id, play_count, finish_count) 
        VALUES (?, 1, 0) 
        ON CONFLICT(file_id) DO UPDATE SET play_count = play_count + 1
    ''', (file_id,))
    conn.commit()
    conn.close()

def increment_finish_count(file_id: str):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO track_stats (file_id, play_count, finish_count) 
        VALUES (?, 0, 1) 
        ON CONFLICT(file_id) DO UPDATE SET finish_count = finish_count + 1
    ''', (file_id,))
    conn.commit()
    conn.close()

def get_all_track_stats() -> dict:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT file_id, play_count, finish_count FROM track_stats')
    rows = c.fetchall()
    stats = {}
    for row in rows:
        stats[row['file_id']] = {'play': row['play_count'], 'finish': row['finish_count']}
    conn.close()
    return stats

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
