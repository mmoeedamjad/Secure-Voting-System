import sqlite3

DB_NAME = "voting.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    # Users table for Authentication and Authorization
    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash INTEGER,
        has_voted INTEGER DEFAULT 0,
        pub_e INTEGER, pub_n INTEGER,
        priv_d INTEGER, priv_n INTEGER,
        role TEXT
    )""")

    # Election details
    db.execute("""
    CREATE TABLE IF NOT EXISTS election (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        options TEXT
    )""")

    # Votes table (Confidentiality via encryption, Non-repudiation via signature)
    db.execute("""
    CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        encrypted_vote TEXT,
        signature INTEGER,
        voter_id TEXT
    )""")
    db.commit()
    db.close()