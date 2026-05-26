import sqlite3

def init_db():
    conn = sqlite3.connect("oneid.db")
    cursor = conn.cursor()

    # Users table (already existing)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            public_key TEXT NOT NULL
        )
    """)

    # NEW: signatures history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signatures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            document TEXT NOT NULL,
            signature TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database created successfully")