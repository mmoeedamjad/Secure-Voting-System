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
        uid = request.form.get("user_id")
        pwd = request.form.get("password")
        
        if not uid or not pwd:
            flash("Please provide both username and password", "error")
            return render_template("login.html")
        
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
    if session.get("role") != "admin": 
        flash("Access denied. Admin only.", "error")
        return redirect("/login")
    return render_template("admin_dashboard.html")

@app.route("/create_voter", methods=["GET", "POST"])
def create_voter():
    if session.get("role") != "admin": 
        flash("Access denied. Admin only.", "error")
        return redirect("/login")
    
    db = get_db()
    
    if request.method == "POST":
        v_id = request.form.get("voter_id")
        v_pw = request.form.get("password")
        selected_elections = request.form.getlist("elections")  # Get multiple elections
        
        if not v_id or not v_pw:
            flash("Please provide both voter ID and password", "error")
            elections = db.execute("SELECT * FROM election").fetchall()
            return render_template("create_voter.html", elections=elections)
        
        if not selected_elections:
            flash("Please select at least one election for this voter", "error")
            elections = db.execute("SELECT * FROM election").fetchall()
            return render_template("create_voter.html", elections=elections)
        
        # Check if username already exists
        existing_user = db.execute("SELECT * FROM users WHERE username=?", (v_id,)).fetchone()
        if existing_user:
            flash(f"Error: Voter '{v_id}' already exists!", "error")
            elections = db.execute("SELECT * FROM election").fetchall()
            return render_template("create_voter.html", elections=elections)
        
        try:
            pub, priv = generate_asymmetric_keys()
            
            # Insert voter
            db.execute("""INSERT INTO users (username, password_hash, pub_e, pub_n, priv_d, priv_n, role) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                       (v_id, simple_hash(v_pw), pub[0], pub[1], priv[0], priv[1], "voter"))
            db.commit()
            
            # Get the voter's ID
            voter = db.execute("SELECT id FROM users WHERE username=?", (v_id,)).fetchone()
            
            # Register voter for selected elections
            for election_id in selected_elections:
                db.execute("""INSERT INTO voter_elections (voter_id, election_id, has_voted) 
                           VALUES (?, ?, 0)""", (voter['id'], election_id))
            db.commit()
            
            flash(f"Voter {v_id} created and registered for {len(selected_elections)} election(s).", "success")
            return redirect("/admin")
            
        except sqlite3.IntegrityError as e:
            flash(f"Database error: {str(e)}", "error")
        except Exception as e:
            flash(f"Error creating voter: {str(e)}", "error")
    
    # GET request - show form with available elections
    elections = db.execute("SELECT * FROM election").fetchall()
    return render_template("create_voter.html", elections=elections)

@app.route("/create_election", methods=["GET", "POST"])
def create_election():
    if session.get("role") != "admin": 
        flash("Access denied. Admin only.", "error")
        return redirect("/login")
    
    if request.method == "POST":
        q = request.form.get("question")
        opt1 = request.form.get("option1")
        opt2 = request.form.get("option2")
        opt3 = request.form.get("option3")
        
        if not q or not opt1 or not opt2 or not opt3:
            flash("Please provide question and all three options", "error")
            return render_template("create_election.html")
        
        opts = f"{opt1},{opt2},{opt3}"
        
        try:
            db = get_db()
            db.execute("INSERT INTO election (question, options) VALUES (?, ?)", (q, opts))
            db.commit()
            flash("Election created successfully.", "success")
            return redirect("/admin")
        except Exception as e:
            flash(f"Error creating election: {str(e)}", "error")
            
    return render_template("create_election.html")

@app.route("/view_voters", methods=["GET", "POST"])
def view_voters():
    if session.get("role") != "admin":
        flash("Access denied. Admin only.", "error")
        return redirect("/login")

    db = get_db()
    elections = db.execute("SELECT * FROM election").fetchall()

    users = []
    selected_election = None

    if request.method == "POST":
        selected_election = request.form.get("election_id")
        
        if selected_election:
            # Get voters registered for this election with their voting status
            users = db.execute("""
                SELECT users.*, voter_elections.has_voted as voted_in_election
                FROM users
                JOIN voter_elections ON users.id = voter_elections.voter_id
                WHERE voter_elections.election_id=? AND users.role='voter'
                ORDER BY voter_elections.has_voted ASC, users.username ASC
            """, (selected_election,)).fetchall()

    return render_template("view_voters.html",
                           elections=elections,
                           users=users,
                           selected_election=selected_election)


@app.route("/vote", methods=["GET", "POST"])
def vote():
    if session.get("role") != "voter":
        flash("Access denied. Voters only.", "error")
        return redirect("/login")

    db = get_db()
    voter = db.execute("SELECT * FROM users WHERE username=?", (session["user"],)).fetchone()

    if not voter:
        flash("Voter not found.", "error")
        return redirect("/logout")

    # Get only elections this voter is registered for and hasn't voted in yet
    elections = db.execute("""
        SELECT election.*, voter_elections.has_voted
        FROM election
        JOIN voter_elections ON election.id = voter_elections.election_id
        WHERE voter_elections.voter_id = ? AND voter_elections.has_voted = 0
    """, (voter["id"],)).fetchall()

    if request.method == "POST":
        election_id = request.form.get("election_id")
        choice = request.form.get("vote_option")
        
        if not election_id or not choice:
            flash("Please select an election and a vote option", "error")
            return render_template("select_election_vote.html", elections=elections)

        # Verify voter is registered for this election
        voter_registration = db.execute(
            "SELECT * FROM voter_elections WHERE voter_id=? AND election_id=?",
            (voter["id"], election_id)
        ).fetchone()
        
        if not voter_registration:
            flash("You are not registered for this election.", "error")
            return render_template("select_election_vote.html", elections=elections)
        
        # Check if already voted
        if voter_registration['has_voted'] == 1:
            return render_template("message.html",
                                   title="Access Denied",
                                   message="You already voted in this election.",
                                   redirect_url="/logout")

        try:
            # Encrypt with Admin Public Key
            admin = db.execute("SELECT pub_e, pub_n FROM users WHERE role='admin'").fetchone()
            
            if not admin:
                flash("Admin not found. Cannot encrypt vote.", "error")
                return render_template("select_election_vote.html", elections=elections)
            
            enc_vote = asymmetric_encrypt((admin['pub_e'], admin['pub_n']), choice)

            # Sign with Voter Private Key
            sig = sign_data((voter['priv_d'], voter['priv_n']), choice)

            # Insert vote
            db.execute("""INSERT INTO votes (encrypted_vote, signature, voter_id, election_id)
                          VALUES (?, ?, ?, ?)""",
                       (str(enc_vote), sig, voter["id"], election_id))
            
            # Mark voter as having voted in this election
            db.execute("""UPDATE voter_elections 
                          SET has_voted = 1 
                          WHERE voter_id = ? AND election_id = ?""",
                       (voter["id"], election_id))
            
            db.commit()

            return render_template("message.html",
                                   title="Success",
                                   message="Vote cast securely. Thank you for participating!",
                                   redirect_url="/logout")
        except Exception as e:
            flash(f"Error casting vote: {str(e)}", "error")
            return render_template("select_election_vote.html", elections=elections)

    return render_template("select_election_vote.html", elections=elections)


@app.route("/results", methods=["GET", "POST"])
def results():
    if session.get("role") != "admin":
        flash("Access denied. Admin only.", "error")
        return redirect("/login")

    db = get_db()
    elections = db.execute("SELECT * FROM election").fetchall()

    decrypted_results = {}
    votes_rows = []
    selected_election = None
    participation_stats = None

    if request.method == "POST":
        selected_election = request.form.get("election_id")
        
        if not selected_election:
            flash("Please select an election", "error")
            return render_template("results.html",
                                   elections=elections,
                                   selected_election=None,
                                   encrypted_data=[],
                                   results={})

        # Get votes
        votes_rows = db.execute(
            "SELECT * FROM votes WHERE election_id=?",
            (selected_election,)
        ).fetchall()

        # Get participation statistics
        stats = db.execute("""
            SELECT 
                COUNT(*) as total_registered,
                SUM(has_voted) as total_voted,
                (COUNT(*) - SUM(has_voted)) as pending
            FROM voter_elections
            WHERE election_id = ?
        """, (selected_election,)).fetchone()
        
        participation_stats = {
            'total_registered': stats['total_registered'],
            'total_voted': stats['total_voted'],
            'pending': stats['pending'],
            'turnout_percentage': (stats['total_voted'] / stats['total_registered'] * 100) if stats['total_registered'] > 0 else 0
        }

        admin = db.execute("SELECT priv_d, priv_n FROM users WHERE role='admin'").fetchone()
        
        if not admin:
            flash("Admin credentials not found. Cannot decrypt votes.", "error")
            return render_template("results.html",
                                   elections=elections,
                                   selected_election=selected_election,
                                   encrypted_data=votes_rows,
                                   results={},
                                   stats=participation_stats)

        for v in votes_rows:
            try:
                cipher_list = ast.literal_eval(v['encrypted_vote'])
                decrypted_data = asymmetric_decrypt((admin['priv_d'], admin['priv_n']), cipher_list)

                if isinstance(decrypted_data, bytes):
                    choice = decrypted_data.decode('utf-8')
                else:
                    choice = str(decrypted_data)

                decrypted_results[choice] = decrypted_results.get(choice, 0) + 1

            except Exception as e:
                print(f"Error decrypting vote ID {v['id']}: {e}")

    return render_template("results.html",
                           elections=elections,
                           selected_election=selected_election,
                           encrypted_data=votes_rows,
                           results=decrypted_results,
                           stats=participation_stats)

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
