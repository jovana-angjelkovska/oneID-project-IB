import hashlib
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding


# create hash of document
def hash_document(data: str):
    return hashlib.sha256(data.encode()).hexdigest()


# sign document using private key
def sign_data(private_key_pem: str, data: str):
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(),
        password=None
    )

    signature = private_key.sign(
        data.encode(),
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    return signature.hex()


# verify signature using public key
def verify_signature(public_key_pem: str, data: str, signature_hex: str):
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode()
    )

    try:
        public_key.verify(
            bytes.fromhex(signature_hex),
            data.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except:
        return False