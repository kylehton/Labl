# Encrypt functions for user tokens
import base64
import hashlib
import os

from cryptography.fernet import Fernet

from dotenv import load_dotenv
load_dotenv()

# Derive a valid Fernet key from env. Set ENCRYPTION_KEY in production.
_SECRET = os.getenv("ENCRYPTION_KEY", "dev-only-change-in-production")
_KEY = base64.urlsafe_b64encode(hashlib.sha256(_SECRET.encode()).digest())
_fernet = Fernet(_KEY)

# Encrypts string
# Returns base64-encoded ciphertext
def encrypt(plaintext: str) -> str:
    return _fernet.encrypt(plaintext.encode()).decode()

def decrypt(ciphertext: str) -> str:
    return _fernet.decrypt(ciphertext.encode()).decode()
