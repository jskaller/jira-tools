
import os, base64, hashlib
from cryptography.fernet import Fernet

def fernet_from_env() -> Fernet:
    """
    Derive a stable Fernet key from APP_SECRET using SHA-256 (urlsafe base64).
    Ensures we always get a valid 32-byte key regardless of APP_SECRET length.
    """
    secret = os.getenv("APP_SECRET", "dev-secret").encode("utf-8")
    digest = hashlib.sha256(secret).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)
