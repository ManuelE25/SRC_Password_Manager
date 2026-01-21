# # storage.py
# import os
# import sqlite3
# from typing import List, Tuple, Optional


# class PasswordDatabase:
#     def __init__(self, db_path: str, encryption_algo: str, key: bytes):
#         self.db_path = db_path
#         self.encryption_algo = encryption_algo  # "aes-gcm" | "chacha20" | "fernet"
#         self.key = key
#         self._init_db()

#     def _init_db(self):
#         conn = sqlite3.connect(self.db_path)
#         cursor = conn.cursor()
#         cursor.execute("""
#             CREATE TABLE IF NOT EXISTS passwords (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 username TEXT NOT NULL,
#                 password TEXT NOT NULL
#             );
#         """)
#         conn.commit()
#         conn.close()

#     @staticmethod
#     def load_or_create_salt(db_path: str) -> bytes:
#         salt_path = db_path + ".salt"
#         if os.path.exists(salt_path):
#             with open(salt_path, "rb") as f:
#                 return f.read()
#         salt = os.urandom(16)
#         with open(salt_path, "wb") as f:
#             f.write(salt)
#         return salt

#     @staticmethod
#     def load_algo(db_path: str) -> Optional[str]:
#         algo_path = db_path + ".algo"
#         if os.path.exists(algo_path):
#             with open(algo_path, "r") as f:
#                 return f.read().strip()
#         return None

#     @staticmethod
#     def save_algo(db_path: str, algo: str) -> None:
#         with open(db_path + ".algo", "w") as f:
#             f.write(algo)

#     def add_password(self, username: str, enc_password: str) -> None:
#         conn = sqlite3.connect(self.db_path)
#         cursor = conn.cursor()
#         cursor.execute(
#             "INSERT INTO passwords (username, password) VALUES (?, ?)",
#             (username, enc_password)
#         )
#         conn.commit()
#         conn.close()

#     def get_password(self, username: str) -> Optional[str]:
#         conn = sqlite3.connect(self.db_path)
#         cursor = conn.cursor()
#         cursor.execute(
#             "SELECT password FROM passwords WHERE username = ?",
#             (username,)
#         )
#         row = cursor.fetchone()
#         conn.close()
#         return row[0] if row else None

#     def list_passwords(self) -> List[Tuple[str, str]]:
#         conn = sqlite3.connect(self.db_path)
#         cursor = conn.cursor()
#         cursor.execute("SELECT username, password FROM passwords")
#         rows = cursor.fetchall()
#         conn.close()
#         return rows

#     def delete_password(self, username: str) -> int:
#         conn = sqlite3.connect(self.db_path)
#         cursor = conn.cursor()
#         cursor.execute(
#             "DELETE FROM passwords WHERE username = ?",
#             (username,)
#         )
#         affected = cursor.rowcount
#         conn.commit()
#         conn.close()

# storage.py
import sqlite3
import os
from typing import List, Tuple, Optional
from crypto_utils import (
    derive_key, 
    encrypt_aes_gcm, decrypt_aes_gcm,
    encrypt_chacha20, decrypt_chacha20,
    encrypt_fernet, decrypt_fernet
)

class InvalidPasswordException(Exception):
    """Exceção personalizada para quando a password mestra está errada."""
    pass

class PasswordDatabase:
    def __init__(self, db_path: str):
        """Inicializa a conexão com a BD, mas não a desbloqueia ainda."""
        self.db_path = db_path
        self.key: Optional[bytes] = None  # A chave fica aqui quando desbloqueada
        self.encryption_algo = "aes-gcm"  # Algoritmo predefinido
        self._init_db_structure()

    def _init_db_structure(self):
        """
        Cria as tabelas necessárias se o ficheiro for novo.
        'metadata': Guarda configurações (Salt, Algo, Validação).
        'passwords': Guarda os dados do utilizador (ambos encriptados).
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value BLOB
            );
        """)
        
        # Nota: 'username' não é UNIQUE aqui porque, quando encriptado, 
        # o mesmo nome gera strings diferentes (devido ao nonce aleatório).
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            );
        """)
        conn.commit()
        conn.close()

    # --- Funções Internas de Criptografia ---
    def _encrypt_data(self, plaintext: str) -> str:
        """Helper que escolhe a função de cifrar correta baseada na configuração."""
        if self.encryption_algo == "aes-gcm":
            return encrypt_aes_gcm(self.key, plaintext)
        elif self.encryption_algo == "chacha20":
            return encrypt_chacha20(self.key, plaintext)
        elif self.encryption_algo == "fernet":
            return encrypt_fernet(self.key, plaintext)
        else:
            raise ValueError(f"Algoritmo não suportado: {self.encryption_algo}")

    def _decrypt_data(self, ciphertext: str) -> str:
        """Helper que escolhe a função de decifrar correta."""
        if self.encryption_algo == "aes-gcm":
            return decrypt_aes_gcm(self.key, ciphertext)
        elif self.encryption_algo == "chacha20":
            return decrypt_chacha20(self.key, ciphertext)
        elif self.encryption_algo == "fernet":
            return decrypt_fernet(self.key, ciphertext)
        else:
            raise ValueError(f"Algoritmo não suportado: {self.encryption_algo}")

    # --- Gestão da Base de Dados ---
    def create_new(self, password: str, algo: str = "aes-gcm"):
        """
        Configura uma base de dados nova.
        1. Gera um Salt aleatório.
        2. Guarda o algoritmo escolhido.
        3. Cria um token de validação encriptado para testar a password no futuro.
        """
        self.encryption_algo = algo
        salt = os.urandom(16)
        key = derive_key(password, salt)
        self.key = key 
        
        # Ciframos a palavra "CHECK_VALID". Se no futuro conseguirmos ler isto, a password está certa.
        validation_token = self._encrypt_data("CHECK_VALID")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Guardamos as configurações na tabela metadata
        cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", ("salt", salt))
        cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", ("algo", algo.encode()))
        cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", ("validation", validation_token.encode()))
        
        conn.commit()
        conn.close()

    def unlock(self, password: str):
        """
        Tenta abrir uma BD existente.
        1. Lê o Salt e o Algoritmo do ficheiro.
        2. Tenta decifrar o token de validação.
        3. Se falhar, levanta InvalidPasswordException.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Recuperar Salt
        cursor.execute("SELECT value FROM metadata WHERE key='salt'")
        row_salt = cursor.fetchone()
        if not row_salt:
            conn.close()
            raise ValueError("Ficheiro inválido ou corrompido (sem Salt).")
        salt = row_salt[0]
        
        # Recuperar Algoritmo
        cursor.execute("SELECT value FROM metadata WHERE key='algo'")
        row_algo = cursor.fetchone()
        if row_algo:
            self.encryption_algo = row_algo[0].decode()
        else:
            self.encryption_algo = "aes-gcm" # Fallback para versões antigas

        # Recuperar Token de Validação
        cursor.execute("SELECT value FROM metadata WHERE key='validation'")
        row_val = cursor.fetchone()
        conn.close()

        # Derivar a chave
        key = derive_key(password, salt)
        self.key = key # Definimos temporariamente

        # Validar
        if row_val:
            validation_token = row_val[0].decode()
            try:
                check = self._decrypt_data(validation_token)
                if check != "CHECK_VALID":
                    raise InvalidPasswordException()
            except Exception:
                self.key = None # Limpa a chave se falhar
                raise InvalidPasswordException("Password incorreta.")
        
        # Se chegou aqui, a chave é válida.

    def add_password(self, username: str, password_text: str) -> None:
        """Cifra o username e a password e insere na BD."""
        if not self.key: raise Exception("Base de dados bloqueada.")
            
        enc_username = self._encrypt_data(username)
        enc_password = self._encrypt_data(password_text)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO passwords (username, password) VALUES (?, ?)", (enc_username, enc_password))
        conn.commit()
        conn.close()

    def list_passwords(self) -> List[Tuple[str, str]]:
        """Lê todas as linhas, decifra e retorna uma lista de tuplos (user, pass)."""
        if not self.key: raise Exception("Base de dados bloqueada.")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT username, password FROM passwords")
        rows = cursor.fetchall()
        conn.close()
        
        decoded_rows = []
        for enc_user, enc_pass in rows:
            try:
                user = self._decrypt_data(enc_user)
                pwd = self._decrypt_data(enc_pass)
                decoded_rows.append((user, pwd))
            except:
                continue # Ignora dados corrompidos
        return decoded_rows

    def get_password(self, target_username: str) -> Optional[str]:
        """Procura um username específico e devolve a password."""
        if not self.key: raise Exception("Base de dados bloqueada.")
        
        # Como o username está encriptado, temos de carregar tudo e procurar na memória
        all_creds = self.list_passwords()
        for user, pwd in all_creds:
            if user == target_username:
                return pwd
        return None

    def delete_password(self, target_username: str) -> int:
        """Encontra o ID correspondente ao username e apaga-o."""
        if not self.key: raise Exception("Base de dados bloqueada.")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM passwords")
        rows = cursor.fetchall()
        
        id_to_delete = None
        for row_id, enc_user in rows:
            try:
                dec_user = self._decrypt_data(enc_user)
                if dec_user == target_username:
                    id_to_delete = row_id
                    break
            except:
                continue
        
        affected = 0
        if id_to_delete:
            cursor.execute("DELETE FROM passwords WHERE id = ?", (id_to_delete,))
            affected = cursor.rowcount
            conn.commit()
            
        conn.close()
        return affected