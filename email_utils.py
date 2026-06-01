import random
import smtplib
from email.mime.text import MIMEText

import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def generate_code():
    return str(random.randint(100000, 999999))


def send_verification_email(receiver_email, code):

    subject = "OneID Verification Code"

    body = f"""
Your OneID verification code is:

{code}

Enter this code inside the application to continue registration.
"""

    msg = MIMEText(body)

    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = receiver_email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:

        server.starttls()

        server.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD
        )

        server.send_message(msg)