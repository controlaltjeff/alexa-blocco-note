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

def save_note(text):
    """Save a note to the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO notes (content) VALUES (?)', (text,))
    conn.commit()
    conn.close()

def get_notes(limit=5):
    """Retrieve the most recent notes."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT content FROM notes ORDER BY timestamp DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_all_notes():
    """Retrieve all notes."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT content FROM notes ORDER BY timestamp DESC')
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]
