from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import random

from Crypto.Cipher import AES
import base64

from crypto_utils import generate_key_pair
from signing import sign_data, verify_signature
import random
from flask import session
from biometric import compare_faces

from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"D:\OCR\ocr\tesseract.exe"

from email_utils import (
    generate_code,
    send_verification_email
)

def generate_oneid():
    return f"ONEID-{random.randint(10000000, 99999999)}"

AES_KEY = b'12345678901234567890123456789012'  # 32 bytes


def encrypt_data(text):

    if not text:
        return None

    cipher = AES.new(AES_KEY, AES.MODE_EAX)

    ciphertext, tag = cipher.encrypt_and_digest(
        str(text).encode()
    )

    encrypted = base64.b64encode(
        cipher.nonce + ciphertext
    ).decode()

    return encrypted


def decrypt_data(encrypted_text):

    if not encrypted_text:
        return None

    data = base64.b64decode(encrypted_text)

    nonce = data[:16]
    ciphertext = data[16:]

    cipher = AES.new(
        AES_KEY,
        AES.MODE_EAX,
        nonce=nonce
    )

    plaintext = cipher.decrypt(ciphertext)

    return plaintext.decode()

app = Flask(__name__)

app.secret_key = "oneid-secret-key"
os.makedirs("keys", exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect("oneid.db")
    conn.row_factory = sqlite3.Row
    return conn

import re


def extract_ocr_text(image_path):
    img = Image.open(image_path)
    img = img.convert("L")

    text = pytesseract.image_to_string(img, lang="mkd+eng")

    print("\n================ OCR =================")
    print(text)
    print("======================================\n")

    return text


def clean(text):
    text = text.upper()
    text = re.sub(r'\s+', ' ', text)
    return text


def get_line_after_label(text, labels):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for i, line in enumerate(lines):
        uline = line.upper()
        for label in labels:
            if label in uline:
                after = line.split(label, 1)[-1].strip(" :-")
                if after:
                    return after
                if i + 1 < len(lines):
                    return lines[i + 1].strip()
    return None


def normalize_value(value):
    if not value:
        return "UNKNOWN"
    value = value.replace("|", " ").replace("/", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value if len(value) > 1 else "UNKNOWN"


def extract_after_patterns(text, patterns):
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def normalize_name(value):
    if not value:
        return "UNKNOWN"

    value = value.upper()
    value = value.replace("|", " ").replace("/", " ")
    value = re.sub(r"[^A-ZА-ЯЃЌЉЊЏ\s]", " ", value, flags=re.UNICODE)
    value = re.sub(r"\s+", " ", value).strip()

    stop_words = {"MKD", "THE", "NAME", "IS", "SURNAME", "GIVEN"}
    parts = [p for p in value.split() if p not in stop_words and len(p) > 1]

    return " ".join(parts) if parts else "UNKNOWN"


def normalize_address(value):
    if not value:
        return "UNKNOWN"

    value = value.upper()
    value = value.replace("|", " ").replace("/", " ")
    value = re.sub(r"\s+", " ", value).strip()

    if value in {"НЕГОТИНО NEGOTINO", "NEGOTINO", "НЕГОТИНО"}:
        return "UNKNOWN"

    stop_words = ["ID CARD NUMBER", "BROJ", "AUTHORITY", "DATE", "ВАЖИ", "EMBG"]
    for word in stop_words:
        if word in value:
            value = value.split(word)[0].strip()

    return value if len(value) > 2 else "UNKNOWN"


def parse_ocr_data(front_text, back_text):

    text = clean(front_text + " " + back_text)

    # ---------------- EMBG ----------------
    embg_match = re.search(r"\b\d{13}\b", text)
    embg = embg_match.group(0) if embg_match else "UNKNOWN"

    # ---------------- DOCUMENT NUMBER ----------------
    doc_match = re.search(
        r"(ID CARD NUMBER|BROJ NA LICHNA KARTA)\s*[:\-]?\s*([A-Z0-9]{5,15})",
        text
    )
    document_number = doc_match.group(2) if doc_match else "UNKNOWN"

    # ======================================================
    # NAME
    # ======================================================
    name_raw = extract_after_patterns(front_text, [
        r"THE NAME IS\s*([A-ZА-ЯЃЌЉЊЏ\s]+)",
        r"NAME IS\s*([A-ZА-ЯЃЌЉЊЏ\s]+)",
        r"(?:GIVEN NAME|IME)\s*[:\-]?\s*([A-ZА-ЯЃЌЉЊЏ\s]+)"
    ])
    first_name = normalize_name(name_raw)

    # ======================================================
    # SURNAME
    # ======================================================
    surname_raw = extract_after_patterns(front_text, [
        r"THE SURNAME IS\s*([A-ZА-ЯЃЌЉЊЏ\s]+)",
        r"SURNAME IS\s*([A-ZА-ЯЃЌЉЊЏ\s]+)",
        r"(?:SURNAME|PREZIME)\s*[:\-]?\s*([A-ZА-ЯЃЌЉЊЏ\s]+)"
    ])
    last_name = normalize_name(surname_raw)

    # ======================================================
    # DATES
    # ======================================================
    birth_match = re.search(
        r"(DATE OF BIRTH|ДАТУМ НА РАЃАЊЕ)\s*[:\-]?\s*(\d{2}[./-]\d{2}[./-]\d{4})",
        text
    )
    birth_date = birth_match.group(2) if birth_match else "UNKNOWN"

    expiry_match = re.search(
        r"(DATE OF EXPIRY|VALID UNTIL|VAZHI DO|ВАЖИ ДО)\s*[:\-]?\s*(\d{2}[./-]\d{2}[./-]\d{4})",
        text,
        re.IGNORECASE
    )
    expiry_date = expiry_match.group(2) if expiry_match else "UNKNOWN"

    # ---------------- GENDER ----------------
    gender = "Male" if " M " in f" {text} " else "Female" if " F " in f" {text} " else "UNKNOWN"

    # ---------------- COUNTRY ----------------
    country = "NORTH MACEDONIA" if "MACEDONIA" in text else "UNKNOWN"

    # ---------------- CITY ----------------
    if "NEGOTINO" in text or "НЕГОТИНО" in text:
        city = "NEGOTINO"
    elif "SKOPJE" in text or "СКОПЈЕ" in text:
        city = "SKOPJE"
    else:
        city = "UNKNOWN"

    # ---------------- ADDRESS ----------------
    address_raw = extract_after_patterns(back_text, [
        r"(?:ADDRESS|PERMANENT RESIDENCE|АДРЕСА|ЖИВЕАЛИШТЕ)\s*[:\-]?\s*([A-ZА-ЯЃЌЉЊЏ0-9\s,./-]+)"
    ])
    address = normalize_address(address_raw)

    return {
        "first_name": first_name,
        "last_name": last_name,
        "embg": embg,
        "document_number": document_number,
        "birth_date": birth_date,
        "gender": gender,
        "country": country,
        "city": city,
        "address": address,
        "expiry_date": expiry_date
    }

@app.route("/")
def home():
    return render_template("index.html")



@app.route("/register", methods=["GET", "POST"])
def register():


    if request.method == "POST":


        import bcrypt


        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        phone = request.form["phone"]


        # 🔐 HASH PASSWORD HERE (IMPORTANT)
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')


        email_code = generate_code()
        phone_code = str(random.randint(100000, 999999))


        # 📦 STORE HASHED PASSWORD IN SESSION (NOT RAW)
        session["registration"] = {
            "user": {
                "username": username,
                "password": hashed_password,
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


        # 🔐 STEP 1: fetch user ONLY by username
        cursor.execute("""
            SELECT * FROM users
            WHERE username = ?
        """, (username,))


        user = cursor.fetchone()


        if not user:
            conn.close()
            return "Invalid username or password"


        # 🔐 STEP 2: verify hashed password
        import bcrypt


        if not bcrypt.checkpw(
            password.encode('utf-8'),
            user["password"].encode('utf-8')
        ):
            conn.close()
            return "Invalid username or password"


        # 📜 Save login history
        cursor.execute("""
            INSERT INTO login_history
            (username, ip_address)
            VALUES (?, ?)
        """, (
            username,
            request.remote_addr
        ))


        conn.commit()
        conn.close()


        session["username"] = username


        # Identity status
        session["verified_identity"] = bool(user["identity_verified"])


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


    # 👤 user profile data
    cursor.execute("""
        SELECT * FROM users WHERE username = ?
    """, (session["username"],))
    user = cursor.fetchone()


    # 📜 last login info (optional but recommended)
    cursor.execute("""
        SELECT login_time, ip_address
        FROM login_history
        WHERE username = ?
        ORDER BY login_time DESC
        LIMIT 2
    """, (session["username"],))


    logins = cursor.fetchall()
    last_login = logins[1] if len(logins) > 1 else None


    conn.close()


    return render_template(
        "dashboard.html",
        user=user,
        last_login=last_login
    )


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
        SELECT login_time, ip_address
        FROM login_history
        WHERE username = ?
        ORDER BY login_time DESC
    """, (session["username"],))


    records = cursor.fetchall()


    conn.close()


    return render_template(
        "history.html",
        records=records
    )


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


        # save temp
        id_front.save("id_front.jpg")
        id_back.save("id_back.jpg")
        selfie.save("selfie.jpg")


        # face check
        from biometric import compare_faces
        result = compare_faces("id_front.jpg", "selfie.jpg")


        # OCR
        front_text = extract_ocr_text("id_front.jpg")
        back_text = extract_ocr_text("id_back.jpg")


        parsed_data = parse_ocr_data(front_text, back_text)

        encrypted_embg = encrypt_data(
        parsed_data["embg"]
    )

        encrypted_address = encrypt_data(
        parsed_data["address"]
    )

        encrypted_document_number = encrypt_data(
        parsed_data["document_number"]
    )

        encrypted_birth_date = encrypt_data(
        parsed_data["birth_date"]
    )

        # delete temp files
        import os
        os.remove("id_front.jpg")
        os.remove("id_back.jpg")
        os.remove("selfie.jpg")


        if not result["match"]:
            return redirect("/identity-result?status=failed")


        # DB save
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
            parsed_data["first_name"],
            parsed_data["last_name"],
            parsed_data["birth_date"],
            parsed_data["gender"],
            parsed_data["embg"],
            parsed_data["document_number"],
            parsed_data["country"],
            parsed_data["city"],
            parsed_data["address"],
            parsed_data["expiry_date"],
            session["username"]
        ))


        conn.commit()
        conn.close()


        session["verified_identity"] = True


        return redirect("/identity-result?status=success")


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


@app.route("/profile")
def profile():


    if "username" not in session:
        return redirect("/login")


    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT *
        FROM users
        WHERE username = ?
    """, (session["username"],))


    user = cursor.fetchone()


    conn.close()


    return render_template(
        "profile.html",
        user=user
    )


if __name__ == "__main__":
     # TEMP DEBUG (remove later)
    import sqlite3
    conn = sqlite3.connect("oneid.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM users")
    print(cursor.fetchall())
    conn.close()

    app.run(debug=True)
