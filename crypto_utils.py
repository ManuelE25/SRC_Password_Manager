# crypto_utils.py
import os, base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())


def encrypt_aes_gcm(key: bytes, plaintext: str) -> str:
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ct).decode()


def decrypt_aes_gcm(key: bytes, ciphertext_b64: str) -> str:
    data = base64.b64decode(ciphertext_b64)
    nonce = data[:12]
    ct = data[12:]
    aesgcm = AESGCM(key)
    pt = aesgcm.decrypt(nonce, ct, None)
    return pt.decode()


def encrypt_chacha20(key: bytes, plaintext: str) -> str:
    chacha = ChaCha20Poly1305(key)
    nonce = os.urandom(12)
    ct = chacha.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ct).decode()


def decrypt_chacha20(key: bytes, ciphertext_b64: str) -> str:
    data = base64.b64decode(ciphertext_b64)
    nonce = data[:12]
    ct = data[12:]
    chacha = ChaCha20Poly1305(key)
    pt = chacha.decrypt(nonce, ct, None)
    return pt.decode()


def encrypt_fernet(key: bytes, plaintext: str) -> str:
    f = Fernet(base64.urlsafe_b64encode(key))
    return f.encrypt(plaintext.encode()).decode()


def decrypt_fernet(key: bytes, ciphertext: str) -> str:
    f = Fernet(base64.urlsafe_b64encode(key))
    return f.decrypt(ciphertext.encode()).decode()
