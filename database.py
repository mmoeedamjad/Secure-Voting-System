import sqlite3

DB_NAME = "voting.db"

def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash INTEGER,
        has_voted INTEGER,
        pub_e INTEGER,
        pub_n INTEGER,
        priv_d INTEGER,
        priv_n INTEGER,
        role TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS election (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        options TEXT,
        status TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        encrypted_vote TEXT,
        vote_hash INTEGER,
        signature INTEGER
    )
    """)

    db.commit()
    db.close()
