import sqlite3

DB_NAME = "voting.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    
    # ================= USERS TABLE =================
    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        has_voted INTEGER DEFAULT 0,
        pub_e INTEGER, 
        pub_n INTEGER,
        priv_d INTEGER, 
        priv_n INTEGER,
        role TEXT
    )""")
    
    # ================= ELECTION TABLE =================
    db.execute("""
    CREATE TABLE IF NOT EXISTS election (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        options TEXT,
        election_name TEXT,
        election_type TEXT,
        start_date TEXT,
        end_date TEXT,
        status TEXT
    )""")
    
    # ================= VOTER-ELECTION RELATION =================
    db.execute("""
    CREATE TABLE IF NOT EXISTS voter_elections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        voter_id INTEGER,
        election_id INTEGER,
        has_voted INTEGER DEFAULT 0,
        FOREIGN KEY (voter_id) REFERENCES users(id),
        FOREIGN KEY (election_id) REFERENCES election(id)
    )""")
    
    # ================= VOTES TABLE =================
    db.execute("""
    CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        election_id INTEGER,
        encrypted_vote TEXT,
        signature INTEGER,
        voter_id INTEGER,
        FOREIGN KEY (voter_id) REFERENCES users(id),
        FOREIGN KEY (election_id) REFERENCES election(id)
    )""")
    
    db.commit()
    db.close()
    print("Database initialized successfully!")

def reset_database():
    """WARNING: This will delete all data! Only use for development/testing."""
    db = get_db()
    db.execute("DROP TABLE IF EXISTS votes")
    db.execute("DROP TABLE IF EXISTS voter_elections")
    db.execute("DROP TABLE IF EXISTS election")
    db.execute("DROP TABLE IF EXISTS users")
    db.commit()
    db.close()
    print("Database reset complete!")
    # init_db()