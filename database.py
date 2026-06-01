import sqlite3

def init_db():
    conn = sqlite3.connect("oneid.db")
    cursor = conn.cursor()

    # 🔐 USERS TABLE (UPDATED FOR FULL AUTH SYSTEM)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,

            email TEXT NOT NULL,
            phone TEXT NOT NULL,

            email_verified INTEGER DEFAULT 0,
            phone_verified INTEGER DEFAULT 0,

            identity_verified INTEGER DEFAULT 0,

            public_key TEXT
        )
    """)

    # 📜 SIGNATURES TABLE
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