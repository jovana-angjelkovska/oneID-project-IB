# 🔐 OneID - Secure Digital Identity System

## 📌 Project Overview
ONEID is a secure web-based digital identity system that enables user registration, identity verification, and electronic document signing.
The system integrates modern technologies such as OCR-based document scanning, biometric verification, and cryptographic digital signatures to ensure authenticity, integrity, and trust in digital interactions.

Users go through a multi-level verification process including identity document validation and selfie-based biometric comparison before being granted access to digital signing features.

---

## 🚀 Features
- User registration with secure credential storage
- Multi-level identity verification system
- Email and phone OTP authentication
- OCR-based automatic extraction of identity document data
- Biometric face verification (ID photo vs selfie)
- Generation of unique ONEID digital identity number
- Secure session-based login system
- Digital document signing and verification

---

## 🛠️ Technologies Used
- Python (Flask) – backend web framework
- SQLite – relational database system
- bcrypt – password hashing and security
- Tesseract OCR – optical character recognition for ID scanning
- Pillow – image preprocessing for OCR
- HTML / CSS / Bootstrap – frontend design
- Jinja2 – server-side templating engine

---

## 🔐 How it works
1. User registers with username, password, email, and phone number
2. System hashes password using bcrypt
3. OTP codes are sent to email and phone for verification
4. User uploads identity card (front and back) and selfie
5. OCR extracts data from identity document automatically
6. System performs biometric comparison between ID photo and selfie
7. If identity is verified, a unique ONEID number is generated
8. User gains access to login system and platform features
9. User can securely sign digital documents using cryptographic methods

---

## 🔒 Security Concept
- bcrypt password hashing
- OTP-based two-factor authentication (email + phone)
- Session-based authentication
- Biometric verification system
- Secure login tracking with IP logging
- Encrypted handling of sensitive user data
 
---

## 📌 Advantages of the System
- High level of security and trust
- Automated identity verification
- Reduced human error in document processing
- Fast and efficient user authentication
- Secure electronic document signing
- Scalable architecture for future improvements
- Centralized digital identity management

---

## 🔮 Future Improvements
- Mobile application version of ONEID
- Advanced AI-based face recognition improvements
- Blockchain-based identity verification
- Document upload and certificate export system
- Enhanced admin dashboard
- Real-time fraud detection system

---

## 👩‍💻 Author
Developed as a university project for Information Security course.
