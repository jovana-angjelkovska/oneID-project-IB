from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import random

from crypto_utils import generate_key_pair
from signing import sign_data, verify_signature
import random 
from flask import session
from biometric import compare_faces

from email_utils import (
    generate_code,
    send_verification_email
)

def generate_oneid():
    return f"ONEID-{random.randint(10000000, 99999999)}"

app = Flask(__name__)

app.secret_key = "oneid-secret-key"
# ensure keys folder exists
os.makedirs("keys", exist_ok=True)


def get_db_connection():
    conn = sqlite3.connect("oneid.db")
    conn.row_factory = sqlite3.Row
    return conn

def simulate_ocr(id_file):
    """
    Fake OCR extraction (for project simulation)
    In real system: this would read passport/ID text.
    """

    # You can randomize or simulate structured extraction
    return {
        "first_name": "John",
        "last_name": "Doe",
        "document_number": str(random.randint(10000000, 99999999)),
        "birth_date": "1999-01-01"
    }

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        phone = request.form["phone"]

        email_code = generate_code()
        phone_code = str(random.randint(100000, 999999))

        session["registration"] = {
            "user": {
                "username": username,
                "password": password,
                "email": email,
                "phone": phone
            },
            "otp_email": email_code,
            "otp_phone": phone_code
        }

        send_verification_email(email, email_code)

        print("📱 PHONE OTP CODE:", phone_code)

        return redirect("/verify-codes")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM users
            WHERE username = ? AND password = ?
        """, (username, password))

        user = cursor.fetchone()
        conn.close()

        if not user:
            return "Invalid username or password"

        session["username"] = username
        session["verified_identity"] = False

        # If user still hasn't done identity verification
        if user["identity_verified"] == 0:
            return redirect("/identity-verification")

        return redirect("/dashboard")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect("/login")

    if not session.get("verified_identity"):
        return redirect("/identity-verification")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM users WHERE username = ?
    """, (session["username"],))

    user = cursor.fetchone()
    conn.close()

    return render_template("dashboard.html", user=user)

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

@app.route("/send-phone-code")
def send_phone_code():

    phone_code = session.get("registration", {}).get("otp_phone")

    if not phone_code:
        return redirect("/register")

    print("📱 PHONE OTP CODE:", phone_code)

    return redirect("/verify-codes")

@app.route("/verify-codes", methods=["GET", "POST"])
def verify_codes():

    data = session.get("registration")

    if not data:
        return "Session expired. Please register again."

    if request.method == "POST":

        email_code = request.form["email_code"].strip()
        phone_code = request.form["phone_code"].strip()

        email_ok = email_code == data.get("otp_email")
        phone_ok = phone_code == data.get("otp_phone")

        print("DEBUG EMAIL:", data.get("otp_email"))
        print("DEBUG PHONE:", data.get("otp_phone"))

        if email_ok and phone_ok:

            user = data["user"]

            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO users (
                    username, password, email, phone,
                    email_verified, phone_verified,
                    identity_verified, public_key
                )
                VALUES (?, ?, ?, ?, 1, 1, 0, NULL)
            """, (
                user["username"],
                user["password"],
                user["email"],
                user["phone"]
            ))

            conn.commit()
            conn.close()

            session["verified_user"] = user
            session.pop("registration", None)

            return redirect("/verified-success")

        return f"Invalid codes → email_ok={email_ok}, phone_ok={phone_ok}"

    return render_template("verify_codes.html")

@app.route("/verified-success")
def verified_success():
    return render_template("verify_success.html")

@app.route("/identity-verification", methods=["GET", "POST"])
def identity_verification():

    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":

        id_front = request.files.get("id_front")
        id_back = request.files.get("id_back")
        selfie = request.files.get("selfie")

        if not id_front or not id_back or not selfie:
            return redirect("/identity-result?status=failed")

        id_front.save("id_front.jpg")
        id_back.save("id_back.jpg")
        selfie.save("selfie.jpg")

        from biometric import compare_faces
        result = compare_faces("id_front.jpg", "selfie.jpg")

        import os
        os.remove("id_front.jpg")
        os.remove("id_back.jpg")
        os.remove("selfie.jpg")

        if result["match"]:

            conn = get_db_connection()
            cursor = conn.cursor()

            oneid_number = generate_oneid()

            cursor.execute("""
                UPDATE users
                SET identity_verified = 1,
                    oneid_number = ?,

                    first_name = ?,
                    last_name = ?,
                    birth_date = ?,
                    gender = ?,
                    embg = ?,
                    document_number = ?,
                    country = ?,
                    city = ?,
                    address = ?,
                    expiry_date = ?

                WHERE username = ?
            """, (
                oneid_number,
                "John",
                "Doe",
                "12.03.2002",
                "Male",
                "1203998450012",
                "AB1234567",
                "North Macedonia",
                "Skopje",
                "Example Street 12",
                "12.03.2032",
                session["username"]
            ))

            conn.commit()
            conn.close()

            session["verified_identity"] = True

            return redirect("/identity-result?status=success")

        else:
            return redirect("/identity-result?status=failed")

    return render_template("identity_verification.html")

@app.route("/identity-verified")
def identity_verified():

    if "username" not in session:
        return redirect("/login")

    status = request.args.get("status", "failed")

    return render_template("identity_verified.html", status=status)

@app.route("/identity-result")
def identity_result():

    if "username" not in session:
        return redirect("/login")

    status = request.args.get("status", "failed")

    if status == "success":
        session["verified_identity"] = True
    else:
        session["verified_identity"] = False

    return render_template("identity_verified.html", status=status)

if __name__ == "__main__":
     # TEMP DEBUG (remove later)
    import sqlite3
    conn = sqlite3.connect("oneid.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM users")
    print(cursor.fetchall())
    conn.close()

    app.run(debug=True)

