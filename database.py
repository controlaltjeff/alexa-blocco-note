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
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id TEXT PRIMARY KEY,
            retention_days INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def set_retention_days(user_id, days):
    """Set the retention period in days for a user."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO user_settings (user_id, retention_days) VALUES (?, ?)', (user_id, days))
    conn.commit()
    conn.close()

def get_retention_days(user_id):
    """Get the retention period in days for a user. Returns None if not set."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT retention_days FROM user_settings WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def cleanup_old_notes(user_id):
    """Delete notes older than the retention period for a user. Returns number of deleted notes."""
    days = get_retention_days(user_id)
    if days is None:
        return 0
        
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # SQLite 'datetime' modifier handles date calculations
    c.execute(f"DELETE FROM notes WHERE user_id = ? AND timestamp < datetime('now', '-{days} days')", (user_id,))
    deleted_count = c.rowcount
    conn.commit()
    conn.close()
    return deleted_count

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
