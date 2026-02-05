from database import init_db, get_db
from crypto import generate_asymmetric_keys, simple_hash

def setup_system():
    init_db()
    db = get_db()
    
    # Generate Admin Keys
    pub, priv = generate_asymmetric_keys()
    admin_pw_hash = simple_hash("admin123")

    try:
        db.execute("""
            INSERT INTO users (username, password_hash, pub_e, pub_n, priv_d, priv_n, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("admin", admin_pw_hash, pub[0], pub[1], priv[0], priv[1], "admin"))
        db.commit()
        print("System Initialized. Admin: admin / admin123")
    except:
        print("System already initialized.")
    finally:
        db.close()

if __name__ == "__main__":
    setup_system()