import sqlite3
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
import os, base64

# Pedir password mestra
def ask_password(prompt):
    root = tk.Tk()
    root.withdraw()
    pw = simpledialog.askstring("Password Mestra", prompt, show="*")
    root.destroy()
    return pw

# Derivar chave da password mestra com PBKDF2HMAC-SHA256
def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

# Guardar ou carregar salt
def load_or_create_salt(db_path):
    salt_path = db_path + ".salt"
    if os.path.exists(salt_path):
        with open(salt_path, 'rb') as f:
            return f.read()
    else:
        salt = os.urandom(16)
        with open(salt_path, 'wb') as f:
            f.write(salt)
        return salt

# Encrypt/decrypt com AES-GCM
def encrypt_aes_gcm(key, plaintext):
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ct).decode()

def decrypt_aes_gcm(key, ciphertext_b64):
    data = base64.b64decode(ciphertext_b64)
    nonce = data[:12]
    ct = data[12:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ct, None)
    return plaintext.decode()

# Encrypt/decrypt com ChaCha20-Poly1305
def encrypt_chacha(key, plaintext):
    chacha = ChaCha20Poly1305(key)
    nonce = os.urandom(12)
    ct = chacha.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ct).decode()

def decrypt_chacha(key, ciphertext_b64):
    data = base64.b64decode(ciphertext_b64)
    nonce = data[:12]
    ct = data[12:]
    chacha = ChaCha20Poly1305(key)
    plaintext = chacha.decrypt(nonce, ct, None)
    return plaintext.decode()

# Encrypt/decrypt com Fernet (simplificado)
def encrypt_fernet(key, plaintext):
    f = Fernet(base64.urlsafe_b64encode(key))
    return f.encrypt(plaintext.encode()).decode()

def decrypt_fernet(key, ciphertext):
    f = Fernet(base64.urlsafe_b64encode(key))
    return f.decrypt(ciphertext.encode()).decode()

# Inicializar base de dados
def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        );
    ''')
    conn.commit()
    conn.close()

# Menu inicial para escolher ação
def start_menu():
    root = tk.Tk()
    root.title("Gestor de Passwords - Menu Inicial")
    root.geometry("350x180")
    root.resizable(False, False)

    action_var = tk.StringVar(value="open")

    def choose_action():
        choice = action_var.get()
        root.destroy()
        if choice == "open":
            open_database()
        else:
            create_database()

    tk.Label(root, text="Escolha uma opção:", font=("Arial", 14)).pack(pady=10)

    tk.Radiobutton(root, text="Abrir base de dados existente", variable=action_var, value="open").pack(anchor="w", padx=30)
    tk.Radiobutton(root, text="Criar nova base de dados", variable=action_var, value="create").pack(anchor="w", padx=30)

    tk.Button(root, text="Continuar", command=choose_action).pack(pady=15)
    root.mainloop()

# Abrir base de dados existente
def open_database():
    global db_path, salt, key, encryption_algo

    db_path = filedialog.askopenfilename(
        title="Seleciona a base de dados",
        filetypes=[("SQLite Database", "*.db"), ("Todos os ficheiros", "*.*")]
    )
    if not db_path:
        messagebox.showinfo("Info", "Nenhuma base de dados selecionada. A aplicação será encerrada.")
        exit()

    salt = load_or_create_salt(db_path)
    algo_path = db_path + ".algo"
    if os.path.exists(algo_path):
        with open(algo_path, "r") as f:
            encryption_algo = f.read().strip()
    else:
        encryption_algo = "aes"

    password = ask_password(f"Introduz a password mestra para '{os.path.basename(db_path)}':")
    if not password:
        exit("Password mestra obrigatória!")

    key = derive_key(password, salt)
    init_db(db_path)
    #launch_app()

# Criar nova base de dados e escolher algoritmo
def create_database():
    global db_path, salt, key, encryption_algo

    db_path = filedialog.asksaveasfilename(
        title="Criar nova base de dados",
        defaultextension=".db",
        filetypes=[("SQLite Database", "*.db"), ("Todos os ficheiros", "*.*")]
    )
    if not db_path:
        messagebox.showinfo("Info", "Nenhuma base de dados criada. A aplicação será encerrada.")
        exit()

    enc_algos = ["aes-256", "chacha20", "fernet"]
    def choose_algo():
        choice = algo_var.get()
        if choice not in enc_algos:
            messagebox.showerror("Erro", "Escolha um algoritmo válido.")
            return
        nonlocal chosen_algo
        chosen_algo = choice
        algo_window.destroy()

    chosen_algo = None
    algo_window = tk.Tk()
    algo_window.title("Escolha o Algoritmo de Encriptação")
    algo_window.geometry("500x300")
    tk.Label(algo_window, text="Escolha o tipo de encriptação:", font=("Arial", 12)).pack(pady=10)
    algo_var = tk.StringVar(value=enc_algos[0])
    for a in enc_algos:
        tk.Radiobutton(algo_window, text=a.upper(), variable=algo_var, value=a).pack(anchor="w", padx=30)
    tk.Button(algo_window, text="Confirmar", command=choose_algo).pack(pady=15)
    algo_window.mainloop()

    encryption_algo = chosen_algo

    with open(db_path + ".algo", "w") as f:
        f.write(encryption_algo)

    salt = load_or_create_salt(db_path)
    password = ask_password("Define a password mestra para esta base de dados:")
    if not password:
        exit("Password mestra obrigatória!")

    key = derive_key(password, salt)
    init_db(db_path)
    #launch_app()

# # Funções principais da app
# def add():
#     username = entryName.get()
#     password = entryPassword.get()
#     if username and password:
#         if encryption_algo == "aes":
#             enc_password = encrypt_aes_gcm(key, password)
#         elif encryption_algo == "chacha":
#             enc_password = encrypt_chacha(key, password)
#         else:
#             enc_password = encrypt_fernet(key, password)
#         conn = sqlite3.connect(db_path)
#         cursor = conn.cursor()
#         cursor.execute("INSERT INTO passwords (username, password) VALUES (?, ?)", (username, enc_password))
#         conn.commit()
#         conn.close()
#         messagebox.showinfo("Sucesso", "Password adicionada!")
#     else:
#         messagebox.showerror("Erro", "Preenche ambos os campos.")

# def get():
#     username = entryName.get()
#     conn = sqlite3.connect(db_path)
#     cursor = conn.cursor()
#     cursor.execute("SELECT password FROM passwords WHERE username = ?", (username,))
#     result = cursor.fetchone()
#     conn.close()
#     if result:
#         try:
#             if encryption_algo == "aes":
#                 dec_password = decrypt_aes_gcm(key, result[0])
#             elif encryption_algo == "chacha":
#                 dec_password = decrypt_chacha(key, result[0])
#             else:
#                 dec_password = decrypt_fernet(key, result[0])
#             messagebox.showinfo("Resultado", f"Password para {username}: {dec_password}")
#         except Exception:
#             messagebox.showerror("Erro", "Password mestra errada ou dados corrompidos!")
#     else:
#         messagebox.showinfo("Resultado", "Utilizador não encontrado.")

# def getlist():
#     conn = sqlite3.connect(db_path)
#     cursor = conn.cursor()
#     cursor.execute("SELECT username, password FROM passwords")
#     rows = cursor.fetchall()
#     conn.close()
#     if rows:
#         mess = "Passwords guardadas:\n"
#         for row in rows:
#             try:
#                 if encryption_algo == "aes":
#                     mess += f"{row[0]}: {decrypt_aes_gcm(key, row[1])}\n"
#                 elif encryption_algo == "chacha":
#                     mess += f"{row[0]}: {decrypt_chacha(key, row[1])}\n"
#                 else:
#                     mess += f"{row[0]}: {decrypt_fernet(key, row[1])}\n"
#             except Exception:
#                 mess += f"{row[0]}: ERRO AO DESENCRIPTAR\n"
#         messagebox.showinfo("Lista de passwords", mess)
#     else:
#         messagebox.showinfo("Lista de passwords", "Nenhuma password encontrada.")

# def delete():
#     username = entryName.get()
#     conn = sqlite3.connect(db_path)
#     cursor = conn.cursor()
#     cursor.execute("DELETE FROM passwords WHERE username = ?", (username,))
#     affected = cursor.rowcount
#     conn.commit()
#     conn.close()
#     if affected:
#         messagebox.showinfo("Sucesso", f"Utilizador {username} eliminado!")
#     else:
#         messagebox.showinfo("INFO", f"Utilizador {username} não encontrado.")

# # Interface principal
# def launch_app():
#     global entryName, entryPassword, app

#     app = tk.Tk()
#     app.geometry("450x210")
#     app.title(f"Gestor de Passwords - Algoritmo: {encryption_algo.upper()}")

#     tk.Label(app, text="Utilizador/Site:").grid(row=0, column=0, padx=15, pady=15)
#     entryName = tk.Entry(app)
#     entryName.grid(row=0, column=1, padx=15, pady=15)

#     tk.Label(app, text="Password:").grid(row=1, column=0, padx=10, pady=5)
#     entryPassword = tk.Entry(app)
#     entryPassword.grid(row=1, column=1, padx=10, pady=5)

#     tk.Button(app, text="Adicionar", command=add).grid(row=2, column=0, padx=15, pady=8, sticky="we")
#     tk.Button(app, text="Pesquisar", command=get).grid(row=2, column=1, padx=15, pady=8, sticky="we")
#     tk.Button(app, text="Listar", command=getlist).grid(row=3, column=0, padx=15, pady=8, sticky="we")
#     tk.Button(app, text="Eliminar", command=delete).grid(row=3, column=1, padx=15, pady=8, sticky="we")

#     app.mainloop()

# Execução inicial
if __name__ == "__main__":
    start_menu()
