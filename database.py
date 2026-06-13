import sqlite3

def init_db():
    conn = sqlite3.connect("oneid.db")
    cursor = conn.cursor()

    # 🔐 USERS TABLE (FINAL STRUCTURE)
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

            public_key TEXT,

            -- 🧠 ONEID IDENTITY DATA
            oneid_number TEXT UNIQUE,
            first_name TEXT,
            last_name TEXT,
            birth_date TEXT,
            gender TEXT,
            embg TEXT,
            document_number TEXT,
            country TEXT,
            city TEXT,
            address TEXT,
            expiry_date TEXT
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

    # 📜 LOGIN HISTORY TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database updated successfully")