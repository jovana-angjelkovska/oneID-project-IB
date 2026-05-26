from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

from crypto_utils import generate_key_pair
from signing import sign_data, verify_signature

app = Flask(__name__)

app.secret_key = "oneid-secret-key"
# ensure keys folder exists
os.makedirs("keys", exist_ok=True)


def get_db_connection():
    conn = sqlite3.connect("oneid.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]

        # ✅ generate real RSA keys
        private_key, public_key = generate_key_pair()

        # save private key to file
        key_filename = f"keys/{username}_private.pem"
        with open(key_filename, "w") as f:
            f.write(private_key)

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, public_key) VALUES (?, ?)",
                (username, public_key)
            )
            conn.commit()
        except:
            return "User already exists"

        conn.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["username"] = username
            return redirect("/dashboard")
        else:
            return "User not found"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/login")
    
    return render_template("dashboard.html", username=session["username"])


@app.route("/sign", methods=["GET", "POST"])
def sign():

    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":

        username = session["username"]
        document = request.form["document"].strip()

        key_path = f"keys/{username}_private.pem"

        if not os.path.exists(key_path):
            return "User key not found"

        with open(key_path, "r") as f:
            private_key = f.read()

        signature = sign_data(private_key, document)

        # ✅ SAVE TO DATABASE HERE (ONLY AFTER SIGNING)
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO signatures (username, document, signature)
            VALUES (?, ?, ?)
        """, (username, document, signature))

        conn.commit()
        conn.close()

        return render_template(
            "sign_result.html",
            username=username,
            document=document,
            signature=signature
        )

    return render_template("sign.html")

@app.route("/verify", methods=["GET", "POST"])
def verify():

    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":

        document = request.form["document"].strip()
        signature = request.form["signature"].strip()

        username = request.form.get("username") or session["username"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT public_key FROM users WHERE username = ?",
            (username,)
        )

        user = cursor.fetchone()

        if not user:
            return "User not found"

        public_key = user["public_key"]

        is_valid = verify_signature(public_key, document, signature)

        return render_template(
            "verify_result.html",
            is_valid=is_valid,
            username=username,
            document=document
        )

    return render_template("verify.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/history")
def history():

    if "username" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT document, signature, timestamp
        FROM signatures
        WHERE username = ?
        ORDER BY timestamp DESC
    """, (session["username"],))

    records = cursor.fetchall()
    conn.close()

    return render_template("history.html", records=records)

@app.route("/debug-signatures")
def debug_signatures():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM signatures")
    data = cursor.fetchall()

    conn.close()

    return str(data)

if __name__ == "__main__":
    app.run(debug=True)

