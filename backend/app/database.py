import sqlite3
from typing import List, Dict, Tuple

DATABASE = "chat_data.db"

def init_db():
    """Initialize the database with required tables."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                chat_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(chat_id) REFERENCES chats(chat_id)
            )
        """)
        conn.commit()

def get_db_connection():
    """Get a connection to the database."""
    conn = sqlite3.connect(DATABASE)
    return conn

def create_chat(chat_id: str, title: str = "New Chat", ):
    """Insert a new chat into the database."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chats (chat_id, title) VALUES (?, ?)", (chat_id, title))
        conn.commit()

def save_message(chat_id: str, role: str, content: str):
    """Save a message to the database."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM messages WHERE chat_id = ? AND role = ? AND content = ?",
            (chat_id, role, content),
        )
        count = cursor.fetchone()[0]

        if count == 0:  
            cursor.execute(
                "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
                (chat_id, role, content),
            )
            print(f"✅ Saved new message for chat_id {chat_id}: role={role}, content={content}")

        conn.commit()

def fetch_chat_messages(chat_id: str) -> List[Dict]:
    """Fetch all messages for a given chat ID."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role, content FROM messages WHERE chat_id = ? ORDER BY created_at", (chat_id,))
        messages = cursor.fetchall()
    return [{"role": role, "content": content} for role, content in messages]

def fetch_all_chats() -> List[Tuple[str, str]]:
    """Fetch all chat IDs and titles."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id, title FROM chats ORDER BY created_at DESC")
        return cursor.fetchall()
    
def delete_all_data():
    """Delete all data from the database."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages")  # Delete all messages
        cursor.execute("DELETE FROM chats")    # Delete all chats
        conn.commit()
        print("All data has been deleted from the database.")

if __name__ == "__main__":
    init_db()
else:
    # Auto-initialize when module is imported
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chats'")
        if not cursor.fetchone():
            init_db()

