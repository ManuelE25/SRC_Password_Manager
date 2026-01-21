# storage.py
import sqlite3
import os
from typing import List, Tuple, Optional, Dict
from crypto_utils import (
    derive_key, 
    encrypt_aes_gcm, decrypt_aes_gcm,
    encrypt_chacha20, decrypt_chacha20,
    encrypt_fernet, decrypt_fernet
)

class InvalidPasswordException(Exception):
    pass

class PasswordDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.key: Optional[bytes] = None
        self.encryption_algo = "aes-gcm"
        self._init_db_structure()

    def _init_db_structure(self):
        """Cria tabelas. Inclui agora a coluna 'folder'."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value BLOB
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder TEXT,
                title TEXT NOT NULL,
                url TEXT,
                username TEXT,
                password TEXT NOT NULL
            );
        """)
        conn.commit()
        conn.close()

    # --- Criptografia Interna ---
    def _encrypt_data(self, plaintext: str) -> str:
        if not plaintext: return ""
        if self.encryption_algo == "aes-gcm": return encrypt_aes_gcm(self.key, plaintext)
        elif self.encryption_algo == "chacha20": return encrypt_chacha20(self.key, plaintext)
        elif self.encryption_algo == "fernet": return encrypt_fernet(self.key, plaintext)
        else: raise ValueError(f"Algoritmo não suportado: {self.encryption_algo}")

    def _decrypt_data(self, ciphertext: str) -> str:
        if not ciphertext: return ""
        if self.encryption_algo == "aes-gcm": return decrypt_aes_gcm(self.key, ciphertext)
        elif self.encryption_algo == "chacha20": return decrypt_chacha20(self.key, ciphertext)
        elif self.encryption_algo == "fernet": return decrypt_fernet(self.key, ciphertext)
        else: raise ValueError(f"Algoritmo não suportado: {self.encryption_algo}")

    # --- Setup ---
    def create_new(self, password: str, algo: str = "aes-gcm"):
        self.encryption_algo = algo
        salt = os.urandom(16)
        key = derive_key(password, salt)
        self.key = key 
        
        validation_token = self._encrypt_data("CHECK_VALID")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", ("salt", salt))
        cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", ("algo", algo.encode()))
        cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", ("validation", validation_token.encode()))
        conn.commit()
        conn.close()

    def unlock(self, password: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM metadata WHERE key='salt'")
        row_salt = cursor.fetchone()
        if not row_salt:
            conn.close()
            raise ValueError("Ficheiro inválido (Salt em falta).")
        salt = row_salt[0]
        
        cursor.execute("SELECT value FROM metadata WHERE key='algo'")
        row_algo = cursor.fetchone()
        if row_algo: self.encryption_algo = row_algo[0].decode()
        else: self.encryption_algo = "aes-gcm"

        cursor.execute("SELECT value FROM metadata WHERE key='validation'")
        row_val = cursor.fetchone()
        conn.close()

        key = derive_key(password, salt)
        self.key = key 

        if row_val:
            validation_token = row_val[0].decode()
            try:
                check = self._decrypt_data(validation_token)
                if check != "CHECK_VALID": raise InvalidPasswordException()
            except Exception:
                self.key = None
                raise InvalidPasswordException("Password incorreta.")

    # --- CRUD (Create, Read, Update, Delete) ---
    def add_entry(self, folder: str, title: str, url: str, username: str, password_text: str) -> None:
        if not self.key: raise Exception("Base de dados bloqueada.")
            
        enc_folder = self._encrypt_data(folder)
        enc_title = self._encrypt_data(title)
        enc_url = self._encrypt_data(url)
        enc_user = self._encrypt_data(username)
        enc_pass = self._encrypt_data(password_text)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO entries (folder, title, url, username, password) VALUES (?, ?, ?, ?, ?)",
            (enc_folder, enc_title, enc_url, enc_user, enc_pass)
        )
        conn.commit()
        conn.close()

    def list_entries(self) -> List[Dict[str, str]]:
        if not self.key: raise Exception("Base de dados bloqueada.")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT folder, title, url, username, password FROM entries")
        rows = cursor.fetchall()
        conn.close()
        
        decoded_list = []
        for enc_folder, enc_title, enc_url, enc_user, enc_pass in rows:
            try:
                decoded_list.append({
                    "folder": self._decrypt_data(enc_folder),
                    "title": self._decrypt_data(enc_title),
                    "url": self._decrypt_data(enc_url),
                    "username": self._decrypt_data(enc_user),
                    "password": self._decrypt_data(enc_pass)
                })
            except:
                continue
        # Ordena por pasta e depois por título
        decoded_list.sort(key=lambda x: (x["folder"], x["title"]))
        return decoded_list

    def get_entry_by_title(self, target_title: str) -> Optional[Dict[str, str]]:
        """Procura uma entrada pelo título exato (em memória)."""
        all_entries = self.list_entries()
        for entry in all_entries:
            if entry["title"] == target_title:
                return entry
        return None

    def delete_entry(self, target_title: str) -> int:
        if not self.key: raise Exception("Base de dados bloqueada.")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM entries")
        rows = cursor.fetchall()
        
        id_to_delete = None
        for row_id, enc_title in rows:
            try:
                dec_title = self._decrypt_data(enc_title)
                if dec_title == target_title:
                    id_to_delete = row_id
                    break
            except:
                continue
        
        affected = 0
        if id_to_delete:
            cursor.execute("DELETE FROM entries WHERE id = ?", (id_to_delete,))
            affected = cursor.rowcount
            conn.commit()
            
        conn.close()
        return affected
    
    def get_all_folders(self) -> List[str]:
        """Retorna uma lista única de todas as pastas existentes para o Combobox."""
        entries = self.list_entries()
        folders = set()
        for e in entries:
            if e["folder"]: 
                folders.add(e["folder"])
        return sorted(list(folders))