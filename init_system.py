from database import init_db, get_db
from crypto import generate_asymmetric_keys, simple_hash

def setup_system():
    init_db()
    db = get_db()
    cur = db.cursor()

    # Create Admin
    pub, priv = generate_asymmetric_keys()
    password = "admin123"
    password_hash = simple_hash(password.encode())

    cur.execute("""
    INSERT OR IGNORE INTO users
    (username, password_hash, has_voted, pub_e, pub_n, priv_d, priv_n, role)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "admin",
        password_hash,
        0,
        pub[0], pub[1],
        priv[0], priv[1],
        "admin"
    ))

    db.commit()
    db.close()
    print("System initialized. Admin credentials: admin / admin123")

if __name__ == "__main__":
    setup_system()
