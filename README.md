# 🔐 OneID - Secure Digital Identity System

## 📌 Project Overview
OneID is a web-based system that provides secure user registration, authentication, and digital document signing using RSA cryptography. 
Users can generate cryptographic key pairs, sign documents digitally, and verify signatures to ensure integrity and authenticity.

---

## 🚀 Features
- User registration with RSA key pair generation
- Secure login system (session-based authentication)
- Digital document signing using private key
- Signature verification using public key
- User-specific secure key storage
- Web interface for signing and verifying documents

---

## 🛠️ Technologies Used
- Python (Flask)
- SQLite (database)
- RSA Cryptography (cryptography library)
- HTML / CSS / Bootstrap
- Jinja2 templating

---

## 📂 Project Structure
oneid-project/
├── app.py
├── crypto_utils.py
├── signing.py
├── database.py
├── templates/
├── static/
├── keys/
├── oneid.db


---

## 🔐 How it works
1. User registers → RSA key pair is generated
2. Private key is securely stored on the server filesystem
3. Public key is stored in the SQLite database
4. User logs in and accesses the dashboard
5. User signs a document using their private key
6. A digital signature is generated using RSA + SHA-256
7. Anyone can verify the signature using the stored public key 

---

## 🔒 Security Concept

This project demonstrates the concept of asymmetric cryptography:

- Private key is used for signing (kept secret)
- Public key is used for verification (shared in database)
- Ensures authenticity, integrity, and non-repudiation of documents

---

## 📌 Future Improvements
- Add signature history tracking
- Upload document files instead of text input
- Export signed documents as certificates
- Multi-user dashboard improvements
- Better UI/UX design enhancements

---

## 👩‍💻 Author
Developed as a university project for Information Security course.
