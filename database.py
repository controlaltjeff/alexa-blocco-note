import sqlite3
import os

DB_NAME = "notes.db"

def init_db():
    """Initialize the database with the notes table."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_note(text, user_id):
    """Save a note to the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO notes (content, user_id) VALUES (?, ?)', (text, user_id))
    conn.commit()
    conn.close()

def get_notes(user_id, limit=5):
    """Retrieve the most recent notes for a specific user with timestamps."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT content, timestamp FROM notes WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?', (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return [(row[0], row[1]) for row in rows]

def get_all_notes(user_id):
    """Retrieve all notes for a specific user with timestamps."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT content, timestamp FROM notes WHERE user_id = ? ORDER BY timestamp DESC', (user_id,))
    rows = c.fetchall()
    conn.close()
    return [(row[0], row[1]) for row in rows]
