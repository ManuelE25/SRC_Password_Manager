# storage.py
import os
import sqlite3
from typing import List, Tuple, Optional


class PasswordDatabase:
    def __init__(self, db_path: str, encryption_algo: str, key: bytes):
        self.db_path = db_path
        self.encryption_algo = encryption_algo  # "aes-gcm" | "chacha20" | "fernet"
        self.key = key
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            );
        """)
        conn.commit()
        conn.close()

    @staticmethod
    def load_or_create_salt(db_path: str) -> bytes:
        salt_path = db_path + ".salt"
        if os.path.exists(salt_path):
            with open(salt_path, "rb") as f:
                return f.read()
        salt = os.urandom(16)
        with open(salt_path, "wb") as f:
            f.write(salt)
        return salt

    @staticmethod
    def load_algo(db_path: str) -> Optional[str]:
        algo_path = db_path + ".algo"
        if os.path.exists(algo_path):
            with open(algo_path, "r") as f:
                return f.read().strip()
        return None

    @staticmethod
    def save_algo(db_path: str, algo: str) -> None:
        with open(db_path + ".algo", "w") as f:
            f.write(algo)

    def add_password(self, username: str, enc_password: str) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO passwords (username, password) VALUES (?, ?)",
            (username, enc_password)
        )
        conn.commit()
        conn.close()

    def get_password(self, username: str) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password FROM passwords WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def list_passwords(self) -> List[Tuple[str, str]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT username, password FROM passwords")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def delete_password(self, username: str) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM passwords WHERE username = ?",
            (username,)
        )
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected
