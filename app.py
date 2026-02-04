from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "super_secret_key"  # required for sessions

# ---------------------------
# TEMP DATA (will be DB later)
# ---------------------------
ADMIN_ID = "admin"
ADMIN_PASSWORD = "admin123"

voters = {}
election = {
    "question": None,
    "options": []
}

encrypted_votes = []


# ---------------------------
# ROUTES
# ---------------------------

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_id = request.form["user_id"]
        password = request.form["password"]

        # Admin login
        if user_id == ADMIN_ID and password == ADMIN_PASSWORD:
            session["role"] = "admin"
            return redirect("/admin")

        # Voter login
        if user_id in voters and voters[user_id]["password"] == password:
            if voters[user_id]["voted"]:
                return render_template(
                    "message.html",
                    title="Access Denied",
                    message="You have already voted.",
                    redirect_url="/login"
                )
            session["role"] = "voter"
            session["user"] = user_id
            return redirect("/vote")

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect("/login")
    return render_template("admin_dashboard.html")


@app.route("/create_voter", methods=["GET", "POST"])
def create_voter():
    if session.get("role") != "admin":
        return redirect("/login")

    if request.method == "POST":
        voter_id = request.form["voter_id"]
        password = request.form["password"]

        voters[voter_id] = {
            "password": password,
            "voted": False
        }

        return render_template(
            "create_voter.html",
            message="Voter created successfully"
        )

    return render_template("create_voter.html")


@app.route("/create_election", methods=["GET", "POST"])
def create_election():
    if session.get("role") != "admin":
        return redirect("/login")

    if request.method == "POST":
        election["question"] = request.form["question"]
        election["options"] = [
            request.form["option1"],
            request.form["option2"]
        ]

        if request.form.get("option3"):
            election["options"].append(request.form["option3"])

        return render_template(
            "create_election.html",
            message="Election created successfully"
        )

    return render_template("create_election.html")


@app.route("/vote", methods=["GET", "POST"])
def vote():
    if session.get("role") != "voter":
        return redirect("/login")

    if request.method == "POST":
        selected_option = request.form["vote_option"]

        # placeholder for encrypted vote
        encrypted_votes.append(f"ENCRYPTED({selected_option})")

        voters[session["user"]]["voted"] = True
        session.clear()

        return render_template(
            "message.html",
            title="Vote Submitted",
            message="Your vote has been securely recorded.",
            redirect_url="/login"
        )

    return render_template(
        "vote.html",
        question=election["question"],
        options=election["options"]
    )


@app.route("/results", methods=["GET", "POST"])
def results():
    if session.get("role") != "admin":
        return redirect("/login")

    results_data = None

    if request.method == "POST":
        # fake decryption logic (will be replaced)
        results_data = {}
        for vote in encrypted_votes:
            option = vote.replace("ENCRYPTED(", "").replace(")", "")
            results_data[option] = results_data.get(option, 0) + 1

    return render_template(
        "results.html",
        encrypted_data=encrypted_votes,
        results=results_data
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------------------
# RUN
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
