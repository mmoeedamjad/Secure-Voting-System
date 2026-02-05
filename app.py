from flask import Flask, render_template, request, redirect, session, flash
from database import get_db
from crypto import *
import ast
import sqlite3

app = Flask(__name__)
app.secret_key = "CIA_SECURITY_VOTING_KEY"

@app.route("/")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uid = request.form["user_id"]
        pwd = request.form["password"]
        h = simple_hash(pwd)
        
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (uid, h)).fetchone()
        
        if user:
            session["user"] = uid
            session["role"] = user["role"]
            return redirect("/admin" if user["role"] == "admin" else "/vote")
        flash("Invalid Credentials", "error")
    return render_template("login.html")

@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin": return redirect("/login")
    return render_template("admin_dashboard.html")

@app.route("/create_voter", methods=["GET", "POST"])
def create_voter():
    if session.get("role") != "admin": return redirect("/login")
    if request.method == "POST":
        v_id = request.form["voter_id"]
        v_pw = request.form["password"]
        pub, priv = generate_asymmetric_keys()
        db = get_db()
        db.execute("""INSERT INTO users (username, password_hash, pub_e, pub_n, priv_d, priv_n, role) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                   (v_id, simple_hash(v_pw), pub[0], pub[1], priv[0], priv[1], "voter"))
        db.commit()
        flash(f"Voter {v_id} created successfully.")
    return render_template("create_voter.html")

@app.route("/create_election", methods=["GET", "POST"])
def create_election():
    if session.get("role") != "admin": return redirect("/login")
    if request.method == "POST":
        q = request.form["question"]
        opts = f"{request.form['option1']},{request.form['option2']},{request.form['option3']}"
        db = get_db()
        db.execute("INSERT INTO election (question, options) VALUES (?, ?)", (q, opts))
        db.commit()
        return render_template("admin_dashboard.html", message=f"Election created successfully.")
    return render_template("create_election.html")

@app.route("/vote", methods=["GET", "POST"])
def vote():
    if session.get("role") != "voter": return redirect("/login")
    db = get_db()
    voter = db.execute("SELECT * FROM users WHERE username=?", (session["user"],)).fetchone()
    
    if voter["has_voted"]:
        return render_template("message.html", title="Access Denied", message="You have already cast your vote.", redirect_url="/logout")

    election = db.execute("SELECT * FROM election ORDER BY id DESC LIMIT 1").fetchone()
    
    if request.method == "POST":
        choice = request.form["vote_option"]
        # Confidentiality: Encrypt vote with Admin's Public Key
        admin = db.execute("SELECT pub_e, pub_n FROM users WHERE role='admin'").fetchone()
        enc_vote = asymmetric_encrypt((admin['pub_e'], admin['pub_n']), choice)
        
        # Non-repudiation: Sign with Voter's Private Key
        sig = sign_data((voter['priv_d'], voter['priv_n']), choice)
        
        db.execute("INSERT INTO votes (encrypted_vote, signature, voter_id) VALUES (?, ?, ?)", 
                   (str(enc_vote), sig, session["user"]))
        db.execute("UPDATE users SET has_voted=1 WHERE username=?", (session["user"],))
        db.commit()
        return render_template("message.html", title="Success", message="Vote cast securely.", redirect_url="/logout")

    options = election["options"].split(",") if election else []
    return render_template("vote.html", question=election["question"], options=options)

@app.route("/results", methods=["GET", "POST"])
def results():
    if session.get("role") != "admin": 
        return redirect("/login")
    
    db = get_db()
    db.row_factory = sqlite3.Row 
    
    # Always fetch votes so the "Encrypted Ledger" stays visible on the page
    votes_rows = db.execute("SELECT * FROM votes").fetchall()
    
    # Fetch admin keys
    admin = db.execute("SELECT priv_d, priv_n FROM users WHERE username=?", ("admin",)).fetchone()
    
    decrypted_results = {}

    if request.method == "POST":
        print(f"Attempting to decrypt {len(votes_rows)} votes...")
        
        for v in votes_rows:
            try:
                # 1. Convert the DB string "[123, 456]" back into a Python list
                cipher_list = ast.literal_eval(v['encrypted_vote'])
                
                # 2. Decrypt using the admin's private key (d, n)
                # Your crypto.py returns a bytes object here
                decrypted_data = asymmetric_decrypt((admin['priv_d'], admin['priv_n']), cipher_list)
                
                # 3. FIX: Convert bytes to string safely
                if isinstance(decrypted_data, bytes):
                    choice = decrypted_data.decode('utf-8')
                else:
                    choice = str(decrypted_data)
                
                decrypted_results[choice] = decrypted_results.get(choice, 0) + 1
                
            except Exception as e:
                print(f"Error decrypting vote ID {v['id']}: {e}")

    # sync: Ensure both 'encrypted_data' and 'results' are passed to the template
    return render_template("results.html", 
                           encrypted_data=votes_rows, 
                           results=decrypted_results)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)