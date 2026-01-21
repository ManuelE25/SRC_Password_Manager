import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog

from storage import PasswordDatabase
from crypto_utils import (
    derive_key,
    encrypt_aes_gcm, decrypt_aes_gcm,
    encrypt_chacha20, decrypt_chacha20,
    encrypt_fernet, decrypt_fernet,
)


# ================= Funções de apoio =================

def ask_master_password(prompt: str) -> str:
    root = tk.Tk()
    root.withdraw()
    pw = simpledialog.askstring("Password Mestra", prompt, show="*")
    root.destroy()
    return pw


def start_menu():
    root = tk.Tk()
    root.title("Gestor de Passwords - Menu Inicial")
    root.geometry("360x180")
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
    tk.Radiobutton(
        root,
        text="Abrir base de dados existente",
        variable=action_var,
        value="open"
    ).pack(anchor="w", padx=30)
    tk.Radiobutton(
        root,
        text="Criar nova base de dados",
        variable=action_var,
        value="create"
    ).pack(anchor="w", padx=30)

    tk.Button(root, text="Continuar", command=choose_action).pack(pady=15)
    root.mainloop()


def open_database():
    db_path = filedialog.askopenfilename(
        title="Seleciona a base de dados",
        filetypes=[("SQLite Database", "*.db"), ("Todos os ficheiros", "*.*")]
    )
    if not db_path:
        messagebox.showinfo("Info", "Nenhuma base de dados selecionada.")
        return

    salt = PasswordDatabase.load_or_create_salt(db_path)
    algo = PasswordDatabase.load_algo(db_path)
    if algo is None:
        algo = "aes-gcm"
        PasswordDatabase.save_algo(db_path, algo)

    password = ask_master_password(f"Introduz a password mestra para '{db_path}':")
    if not password:
        messagebox.showerror("Erro", "Password mestra obrigatória!")
        return

    key = derive_key(password, salt)
    pdb = PasswordDatabase(db_path, algo, key)
    launch_app(pdb)


def create_database():
    db_path = filedialog.asksaveasfilename(
        title="Criar nova base de dados",
        defaultextension=".db",
        filetypes=[("SQLite Database", "*.db"), ("Todos os ficheiros", "*.*")]
    )
    if not db_path:
        messagebox.showinfo("Info", "Nenhuma base de dados criada.")
        return

    # Para já, fixamos AES-GCM; se quiseres, depois podemos adicionar o menu de escolha de algoritmo
    algo = "aes-gcm"
    PasswordDatabase.save_algo(db_path, algo)
    salt = PasswordDatabase.load_or_create_salt(db_path)

    password = ask_master_password("Define a password mestra para esta base de dados:")
    if not password:
        messagebox.showerror("Erro", "Password mestra obrigatória!")
        return

    key = derive_key(password, salt)
    pdb = PasswordDatabase(db_path, algo, key)
    launch_app(pdb)


# ================= Interface principal =================

def launch_app(pdb: PasswordDatabase):
    app = tk.Tk()
    app.geometry("700x260")
    app.title(f"Gestor de Passwords - {pdb.encryption_algo.upper()}")

    # --- Painel esquerdo: lista de websites/utilizadores ---
    frame_left = tk.Frame(app)
    frame_left.grid(row=0, column=0, rowspan=4, padx=10, pady=10, sticky="ns")

    tk.Label(frame_left, text="Websites / Utilizadores").pack(anchor="w")

    listbox_sites = tk.Listbox(frame_left, width=30, height=10)
    listbox_sites.pack(side="left", fill="y")

    scrollbar = tk.Scrollbar(frame_left, orient="vertical", command=listbox_sites.yview)
    scrollbar.pack(side="right", fill="y")
    listbox_sites.config(yscrollcommand=scrollbar.set)

    # --- Painel direito: formulário de adição/edição ---
    frame_right = tk.Frame(app)
    frame_right.grid(row=0, column=1, padx=10, pady=10, sticky="n")

    tk.Label(frame_right, text="Website / Utilizador:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    entry_name = tk.Entry(frame_right, width=35)
    entry_name.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(frame_right, text="Password:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    entry_password = tk.Entry(frame_right, width=35, show="*")
    entry_password.grid(row=1, column=1, padx=5, pady=5)

    # --- Funções de cifrar/decifrar ---
    def do_encrypt(plaintext: str) -> str:
        if pdb.encryption_algo == "aes-gcm":
            return encrypt_aes_gcm(pdb.key, plaintext)
        elif pdb.encryption_algo == "chacha20":
            return encrypt_chacha20(pdb.key, plaintext)
        else:
            return encrypt_fernet(pdb.key, plaintext)

    def do_decrypt(ciphertext: str) -> str:
        if pdb.encryption_algo == "aes-gcm":
            return decrypt_aes_gcm(pdb.key, ciphertext)
        elif pdb.encryption_algo == "chacha20":
            return decrypt_chacha20(pdb.key, ciphertext)
        else:
            return decrypt_fernet(pdb.key, ciphertext)

    # --- Gestão da lista lateral ---
    def refresh_list():
        listbox_sites.delete(0, tk.END)
        rows = pdb.list_passwords()
        for username, _ in rows:
            listbox_sites.insert(tk.END, username)

    def add():
        username = entry_name.get().strip()
        password = entry_password.get()
        if not username or not password:
            messagebox.showerror("Erro", "Preenche ambos os campos.")
            return
        enc_password = do_encrypt(password)
        pdb.add_password(username, enc_password)
        messagebox.showinfo("Sucesso", "Password adicionada!")
        refresh_list()

    def show_selected(event=None):
        selection = listbox_sites.curselection()
        if not selection:
            return
        username = listbox_sites.get(selection[0])
        enc = pdb.get_password(username)
        if enc is None:
            messagebox.showinfo("Resultado", "Utilizador não encontrado.")
            return
        try:
            dec = do_decrypt(enc)
            entry_name.delete(0, tk.END)
            entry_name.insert(0, username)
            entry_password.delete(0, tk.END)
            entry_password.insert(0, dec)
        except Exception:
            messagebox.showerror("Erro", "Password mestra errada ou dados corrompidos.")

    def delete():
        selection = listbox_sites.curselection()
        if selection:
            username = listbox_sites.get(selection[0])
        else:
            username = entry_name.get().strip()
        if not username:
            messagebox.showerror("Erro", "Seleciona ou indica o website/utilizador.")
            return
        affected = pdb.delete_password(username)
        if affected:
            messagebox.showinfo("Sucesso", f"Utilizador {username} eliminado!")
            refresh_list()
            entry_name.delete(0, tk.END)
            entry_password.delete(0, tk.END)
        else:
            messagebox.showinfo("INFO", f"Utilizador {username} não encontrado.")

    # Botões (sem botão de Listar)
    tk.Button(frame_right, text="Adicionar / Atualizar", command=add).grid(
        row=2, column=0, padx=5, pady=10, sticky="we"
    )
    tk.Button(frame_right, text="Eliminar", command=delete).grid(
        row=2, column=1, padx=5, pady=10, sticky="we"
    )

    # Clique na lista → mostra credenciais à direita
    listbox_sites.bind("<<ListboxSelect>>", show_selected)

    refresh_list()
    app.mainloop()


# ================= Ponto de entrada =================

if __name__ == "__main__":
    start_menu()
