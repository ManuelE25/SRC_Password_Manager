# import tkinter as tk
# from tkinter import simpledialog, messagebox, filedialog

# from storage import PasswordDatabase
# from crypto_utils import (
#     derive_key,
#     encrypt_aes_gcm, decrypt_aes_gcm,
#     encrypt_chacha20, decrypt_chacha20,
#     encrypt_fernet, decrypt_fernet,
# )


# # ================= Funções de apoio =================

# def ask_master_password(prompt: str) -> str:
#     root = tk.Tk()
#     root.withdraw()
#     pw = simpledialog.askstring("Password Mestra", prompt, show="*")
#     root.destroy()
#     return pw


# def start_menu():
#     root = tk.Tk()
#     root.title("Gestor de Passwords - Menu Inicial")
#     root.geometry("360x180")
#     root.resizable(False, False)

#     action_var = tk.StringVar(value="open")

#     def choose_action():
#         choice = action_var.get()
#         root.destroy()
#         if choice == "open":
#             open_database()
#         else:
#             create_database()

#     tk.Label(root, text="Escolha uma opção:", font=("Arial", 14)).pack(pady=10)
#     tk.Radiobutton(
#         root,
#         text="Abrir base de dados existente",
#         variable=action_var,
#         value="open"
#     ).pack(anchor="w", padx=30)
#     tk.Radiobutton(
#         root,
#         text="Criar nova base de dados",
#         variable=action_var,
#         value="create"
#     ).pack(anchor="w", padx=30)

#     tk.Button(root, text="Continuar", command=choose_action).pack(pady=15)
#     root.mainloop()


# def open_database():
#     db_path = filedialog.askopenfilename(
#         title="Seleciona a base de dados",
#         filetypes=[("SQLite Database", "*.db"), ("Todos os ficheiros", "*.*")]
#     )
#     if not db_path:
#         messagebox.showinfo("Info", "Nenhuma base de dados selecionada.")
#         return

#     salt = PasswordDatabase.load_or_create_salt(db_path)
#     algo = PasswordDatabase.load_algo(db_path)
#     if algo is None:
#         algo = "aes-gcm"
#         PasswordDatabase.save_algo(db_path, algo)

#     password = ask_master_password(f"Introduz a password mestra para '{db_path}':")
#     if not password:
#         messagebox.showerror("Erro", "Password mestra obrigatória!")
#         return

#     key = derive_key(password, salt)
#     pdb = PasswordDatabase(db_path, algo, key)
#     launch_app(pdb)


# def create_database():
#     db_path = filedialog.asksaveasfilename(
#         title="Criar nova base de dados",
#         defaultextension=".db",
#         filetypes=[("SQLite Database", "*.db"), ("Todos os ficheiros", "*.*")]
#     )
#     if not db_path:
#         messagebox.showinfo("Info", "Nenhuma base de dados criada.")
#         return

#     # Para já, fixamos AES-GCM; se quiseres, depois podemos adicionar o menu de escolha de algoritmo
#     algo = "aes-gcm"
#     PasswordDatabase.save_algo(db_path, algo)
#     salt = PasswordDatabase.load_or_create_salt(db_path)

#     password = ask_master_password("Define a password mestra para esta base de dados:")
#     if not password:
#         messagebox.showerror("Erro", "Password mestra obrigatória!")
#         return

#     key = derive_key(password, salt)
#     pdb = PasswordDatabase(db_path, algo, key)
#     launch_app(pdb)


# # ================= Interface principal =================

# def launch_app(pdb: PasswordDatabase):
#     app = tk.Tk()
#     app.geometry("700x260")
#     app.title(f"Gestor de Passwords - {pdb.encryption_algo.upper()}")

#     # --- Painel esquerdo: lista de websites/utilizadores ---
#     frame_left = tk.Frame(app)
#     frame_left.grid(row=0, column=0, rowspan=4, padx=10, pady=10, sticky="ns")

#     tk.Label(frame_left, text="Websites / Utilizadores").pack(anchor="w")

#     listbox_sites = tk.Listbox(frame_left, width=30, height=10)
#     listbox_sites.pack(side="left", fill="y")

#     scrollbar = tk.Scrollbar(frame_left, orient="vertical", command=listbox_sites.yview)
#     scrollbar.pack(side="right", fill="y")
#     listbox_sites.config(yscrollcommand=scrollbar.set)

#     # --- Painel direito: formulário de adição/edição ---
#     frame_right = tk.Frame(app)
#     frame_right.grid(row=0, column=1, padx=10, pady=10, sticky="n")

#     tk.Label(frame_right, text="Website / Utilizador:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
#     entry_name = tk.Entry(frame_right, width=35)
#     entry_name.grid(row=0, column=1, padx=5, pady=5)

#     tk.Label(frame_right, text="Password:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
#     entry_password = tk.Entry(frame_right, width=35, show="*")
#     entry_password.grid(row=1, column=1, padx=5, pady=5)

#     # --- Funções de cifrar/decifrar ---
#     def do_encrypt(plaintext: str) -> str:
#         if pdb.encryption_algo == "aes-gcm":
#             return encrypt_aes_gcm(pdb.key, plaintext)
#         elif pdb.encryption_algo == "chacha20":
#             return encrypt_chacha20(pdb.key, plaintext)
#         else:
#             return encrypt_fernet(pdb.key, plaintext)

#     def do_decrypt(ciphertext: str) -> str:
#         if pdb.encryption_algo == "aes-gcm":
#             return decrypt_aes_gcm(pdb.key, ciphertext)
#         elif pdb.encryption_algo == "chacha20":
#             return decrypt_chacha20(pdb.key, ciphertext)
#         else:
#             return decrypt_fernet(pdb.key, ciphertext)

#     # --- Gestão da lista lateral ---
#     def refresh_list():
#         listbox_sites.delete(0, tk.END)
#         rows = pdb.list_passwords()
#         for username, _ in rows:
#             listbox_sites.insert(tk.END, username)

#     def add():
#         username = entry_name.get().strip()
#         password = entry_password.get()
#         if not username or not password:
#             messagebox.showerror("Erro", "Preenche ambos os campos.")
#             return
#         enc_password = do_encrypt(password)
#         pdb.add_password(username, enc_password)
#         messagebox.showinfo("Sucesso", "Password adicionada!")
#         refresh_list()

#     def show_selected(event=None):
#         selection = listbox_sites.curselection()
#         if not selection:
#             return
#         username = listbox_sites.get(selection[0])
#         enc = pdb.get_password(username)
#         if enc is None:
#             messagebox.showinfo("Resultado", "Utilizador não encontrado.")
#             return
#         try:
#             dec = do_decrypt(enc)
#             entry_name.delete(0, tk.END)
#             entry_name.insert(0, username)
#             entry_password.delete(0, tk.END)
#             entry_password.insert(0, dec)
#         except Exception:
#             messagebox.showerror("Erro", "Password mestra errada ou dados corrompidos.")

#     def delete():
#         selection = listbox_sites.curselection()
#         if selection:
#             username = listbox_sites.get(selection[0])
#         else:
#             username = entry_name.get().strip()
#         if not username:
#             messagebox.showerror("Erro", "Seleciona ou indica o website/utilizador.")
#             return
#         affected = pdb.delete_password(username)
#         if affected:
#             messagebox.showinfo("Sucesso", f"Utilizador {username} eliminado!")
#             refresh_list()
#             entry_name.delete(0, tk.END)
#             entry_password.delete(0, tk.END)
#         else:
#             messagebox.showinfo("INFO", f"Utilizador {username} não encontrado.")

#     # Botões (sem botão de Listar)
#     tk.Button(frame_right, text="Adicionar / Atualizar", command=add).grid(
#         row=2, column=0, padx=5, pady=10, sticky="we"
#     )
#     tk.Button(frame_right, text="Eliminar", command=delete).grid(
#         row=2, column=1, padx=5, pady=10, sticky="we"
#     )

#     # Clique na lista → mostra credenciais à direita
#     listbox_sites.bind("<<ListboxSelect>>", show_selected)

#     refresh_list()
#     app.mainloop()

import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog, ttk
import secrets
import string
import math
import time
import pyperclip  # Requer: pip install pyperclip

from storage import PasswordDatabase, InvalidPasswordException

# ================= Lógica de Segurança e Matemática =================

def calculate_entropy(password: str) -> float:
    """
    Calcula a entropia (bits) da password.
    Fórmula: E = L * log2(R)
    """
    if not password:
        return 0
    
    pool_size = 0
    if any(c.islower() for c in password): pool_size += 26
    if any(c.isupper() for c in password): pool_size += 26
    if any(c.isdigit() for c in password): pool_size += 10
    if any(c in string.punctuation for c in password): pool_size += 32
    
    if pool_size == 0:
        return 0
        
    entropy = len(password) * math.log2(pool_size)
    return entropy

def generate_strong_password(length=16, use_upper=True, use_digits=True, use_symbols=True) -> str:
    """Gera uma password segura usando a biblioteca 'secrets'."""
    chars = string.ascii_lowercase
    if use_upper: chars += string.ascii_uppercase
    if use_digits: chars += string.digits
    if use_symbols: chars += string.punctuation

    if not chars:
        return ""

    return ''.join(secrets.choice(chars) for _ in range(length))

# ================= Janelas de Diálogo Auxiliares =================

def ask_master_password(prompt: str) -> str:
    root = tk.Tk()
    root.withdraw()
    pw = simpledialog.askstring("Segurança", prompt, show="*")
    root.destroy()
    return pw

def ask_new_db_config(title: str):
    """Janela para configurar nova BD (Password + Algoritmo)."""
    dialog = tk.Tk()
    dialog.title(title)
    dialog.geometry("300x230")
    dialog.resizable(False, False)
    
    result = {"password": None, "algo": "aes-gcm"}
    
    tk.Label(dialog, text="Password Mestra:").pack(pady=(15, 5))
    entry_pw = tk.Entry(dialog, show="*", width=25)
    entry_pw.pack(pady=5)
    
    tk.Label(dialog, text="Algoritmo de Encriptação:").pack(pady=(10, 5))
    combo_algo = ttk.Combobox(dialog, values=["aes-gcm", "chacha20", "fernet"], state="readonly")
    combo_algo.current(0)
    combo_algo.pack(pady=5)
    
    def on_confirm():
        pw = entry_pw.get()
        if not pw:
            messagebox.showerror("Erro", "A password não pode ser vazia.", parent=dialog)
            return
        result["password"] = pw
        result["algo"] = combo_algo.get()
        dialog.destroy()
        
    def on_cancel():
        dialog.destroy()
        
    frame_btns = tk.Frame(dialog)
    frame_btns.pack(pady=20)
    tk.Button(frame_btns, text="Criar Cofre", command=on_confirm, width=12, bg="#ddffdd").pack(side="left", padx=10)
    tk.Button(frame_btns, text="Cancelar", command=on_cancel, width=10).pack(side="left", padx=10)
    
    dialog.mainloop()
    return result["password"], result["algo"]

def open_generator_dialog(parent):
    """Janela flutuante para gerar passwords."""
    top = tk.Toplevel(parent)
    top.title("Gerador")
    top.geometry("350x300")
    top.resizable(False, False)
    
    var_len = tk.IntVar(value=16)
    var_upper = tk.BooleanVar(value=True)
    var_digits = tk.BooleanVar(value=True)
    var_symbols = tk.BooleanVar(value=True)
    
    generated_pw = tk.StringVar()

    tk.Label(top, text="Comprimento:").pack(pady=(10, 0))
    tk.Scale(top, from_=8, to=64, orient="horizontal", variable=var_len, length=200).pack()
    
    frame_checks = tk.Frame(top)
    frame_checks.pack(pady=5)
    tk.Checkbutton(frame_checks, text="A-Z", variable=var_upper).pack(anchor="w")
    tk.Checkbutton(frame_checks, text="0-9", variable=var_digits).pack(anchor="w")
    tk.Checkbutton(frame_checks, text="!@#", variable=var_symbols).pack(anchor="w")

    entry_result = tk.Entry(top, textvariable=generated_pw, width=30, justify="center", font=("Consolas", 10))
    entry_result.pack(pady=10)

    def run_generate():
        pw = generate_strong_password(
            length=var_len.get(),
            use_upper=var_upper.get(),
            use_digits=var_digits.get(),
            use_symbols=var_symbols.get()
        )
        generated_pw.set(pw)

    def accept():
        top.destroy()
        
    tk.Button(top, text="Gerar Nova", command=run_generate).pack(pady=2)
    tk.Button(top, text="Usar esta Password", command=accept, bg="#ddffdd", height=2).pack(pady=10)
    
    run_generate() # Gera uma ao abrir
    parent.wait_window(top)
    return generated_pw.get()

# ================= Menus de Entrada (Start/Open/Create) =================

def start_menu():
    root = tk.Tk()
    root.title("Gestor Seguro")
    root.geometry("360x200")
    root.resizable(False, False)

    action_var = tk.StringVar(value="open")

    def choose_action():
        choice = action_var.get()
        root.destroy()
        if choice == "open":
            open_database()
        else:
            create_database()

    tk.Label(root, text="Bem-vindo ao Gestor de Passwords", font=("Arial", 12, "bold")).pack(pady=15)
    
    frame_opts = tk.Frame(root)
    frame_opts.pack(pady=5)
    tk.Radiobutton(frame_opts, text="Abrir base de dados existente", variable=action_var, value="open").pack(anchor="w")
    tk.Radiobutton(frame_opts, text="Criar nova base de dados", variable=action_var, value="create").pack(anchor="w")

    tk.Button(root, text="Continuar", command=choose_action, width=20).pack(pady=20)
    root.mainloop()

def open_database():
    db_path = filedialog.askopenfilename(title="Abrir ficheiro cofre", filetypes=[("Cofre Seguro", "*.db")])
    if not db_path:
        start_menu()
        return

    password = ask_master_password(f"Introduz a password mestra:")
    if not password:
        start_menu()
        return

    pdb = PasswordDatabase(db_path)
    try:
        pdb.unlock(password)
        launch_app(pdb)
    except InvalidPasswordException:
        messagebox.showerror("Acesso Negado", "Password Mestra Incorreta!")
        start_menu()
    except Exception as e:
        messagebox.showerror("Erro Crítico", f"Erro: {e}")
        start_menu()

def create_database():
    db_path = filedialog.asksaveasfilename(title="Guardar novo cofre", defaultextension=".db", filetypes=[("Cofre Seguro", "*.db")])
    if not db_path:
        start_menu()
        return

    password, algo = ask_new_db_config("Configurar Nova Base de Dados")
    if not password:
        start_menu()
        return

    pdb = PasswordDatabase(db_path)
    try:
        pdb.create_new(password, algo=algo)
        messagebox.showinfo("Sucesso", f"Cofre criado com encriptação {algo.upper()}!")
        launch_app(pdb)
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao criar: {e}")
        start_menu()

# ================= Aplicação Principal =================

def launch_app(pdb: PasswordDatabase):
    app = tk.Tk()
    app.geometry("800x450") # Aumentei um pouco a altura para acomodar o botão Sair
    app.title(f"Cofre Digital - {pdb.encryption_algo.upper()}")

    # --- Estilos para Barras Coloridas ---
    style = ttk.Style()
    style.theme_use('clam') 
    
    style.configure("Red.Horizontal.TProgressbar", foreground='red', background='red')
    style.configure("Yellow.Horizontal.TProgressbar", foreground='#FFAA00', background='#FFAA00')
    style.configure("Green.Horizontal.TProgressbar", foreground='green', background='green')

    # --- Bloqueio por Inatividade (5 min) ---
    last_activity = time.time()
    LOCK_TIMEOUT = 300 

    def reset_timer(event):
        nonlocal last_activity
        last_activity = time.time()

    def check_inactivity():
        if time.time() - last_activity > LOCK_TIMEOUT:
            app.destroy()
            messagebox.showinfo("Bloqueado", "Sessão expirada por inatividade.")
            start_menu()
        else:
            app.after(1000, check_inactivity)

    app.bind_all("<Any-KeyPress>", reset_timer)
    app.bind_all("<Any-Button>", reset_timer)
    app.after(1000, check_inactivity)

    # --- Layout ---
    frame_left = tk.Frame(app)
    frame_left.grid(row=0, column=0, rowspan=4, padx=10, pady=10, sticky="ns")

    tk.Label(frame_left, text="Contas Guardadas").pack(anchor="w")

    listbox_sites = tk.Listbox(frame_left, width=35, height=18)
    listbox_sites.pack(side="left", fill="y")
    scrollbar = tk.Scrollbar(frame_left, orient="vertical", command=listbox_sites.yview)
    scrollbar.pack(side="right", fill="y")
    listbox_sites.config(yscrollcommand=scrollbar.set)

    frame_right = tk.Frame(app)
    frame_right.grid(row=0, column=1, padx=10, pady=10, sticky="n")

    # Campos de input
    tk.Label(frame_right, text="Website / Utilizador:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    entry_name = tk.Entry(frame_right, width=40)
    entry_name.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(frame_right, text="Password:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    entry_password = tk.Entry(frame_right, width=40, show="*")
    entry_password.grid(row=1, column=1, padx=5, pady=5)

    # --- Funcionalidade: Entropia Visual ---
    lbl_entropy_text = tk.Label(frame_right, text="Força: N/A", font=("Arial", 8, "bold"))
    lbl_entropy_text.grid(row=2, column=1, sticky="w", padx=5)
    
    progress_entropy = ttk.Progressbar(frame_right, orient="horizontal", length=240, mode="determinate", style="Green.Horizontal.TProgressbar")
    progress_entropy.grid(row=3, column=1, sticky="w", padx=5, pady=(0, 10))

    def update_entropy(event=None):
        pwd = entry_password.get()
        bits = calculate_entropy(pwd)
        
        progress_entropy["value"] = min(bits, 100)
        
        if bits < 40:
            progress_entropy.config(style="Red.Horizontal.TProgressbar")
            color_text = "red"
            text = f"Fraca ({int(bits)} bits)"
        elif bits < 80:
            progress_entropy.config(style="Yellow.Horizontal.TProgressbar")
            color_text = "#FFAA00"
            text = f"Média ({int(bits)} bits)"
        else:
            progress_entropy.config(style="Green.Horizontal.TProgressbar")
            color_text = "green"
            text = f"Forte ({int(bits)} bits)"
            
        lbl_entropy_text.config(text=text, fg=color_text)

    entry_password.bind("<KeyRelease>", update_entropy)

    # --- Barra de Ferramentas (Olho, Gerar, Copiar) ---
    frame_tools = tk.Frame(frame_right)
    frame_tools.grid(row=1, column=2, padx=5, sticky="w")

    # 1. Olho
    def toggle_pw():
        if entry_password.cget('show') == '':
            entry_password.config(show='*')
        else:
            entry_password.config(show='')
    tk.Button(frame_tools, text="👁", command=toggle_pw, width=3).pack(side="left", padx=1)

    # 2. Gerar
    def call_generator():
        new_pw = open_generator_dialog(app)
        if new_pw:
            entry_password.delete(0, tk.END)
            entry_password.insert(0, new_pw)
            update_entropy() 
    tk.Button(frame_tools, text="⚙ Gerar", command=call_generator).pack(side="left", padx=1)
    
    # 3. Copiar
    def copy_to_clipboard():
        pwd = entry_password.get()
        if not pwd: return
        pyperclip.copy(pwd)
        messagebox.showinfo("Clipboard", "Password copiada!\nSerá limpa em 30 segundos.")
        
        def clear_clip():
            if pyperclip.paste() == pwd:
                pyperclip.copy("")
                
        app.after(30000, clear_clip)

    tk.Button(frame_tools, text="📋", command=copy_to_clipboard).pack(side="left", padx=1)

    # --- Lógica CRUD ---
    def refresh_list():
        listbox_sites.delete(0, tk.END)
        rows = pdb.list_passwords()
        for username, _ in rows:
            listbox_sites.insert(tk.END, username)

    def add_or_update():
        username = entry_name.get().strip()
        password = entry_password.get()
        if not username or not password:
            messagebox.showwarning("Atenção", "Preenche ambos os campos.")
            return
        try:
            pdb.delete_password(username)
            pdb.add_password(username, password)
            messagebox.showinfo("Guardado", "Credenciais guardadas com segurança.")
            refresh_list()
            entry_name.delete(0, tk.END)
            entry_password.delete(0, tk.END)
            update_entropy()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def show_selected(event=None):
        selection = listbox_sites.curselection()
        if not selection: return
        username = listbox_sites.get(selection[0])
        dec_pass = pdb.get_password(username)
        if dec_pass is not None:
            entry_name.delete(0, tk.END)
            entry_name.insert(0, username)
            entry_password.delete(0, tk.END)
            entry_password.insert(0, dec_pass)
            update_entropy()

    def delete_entry():
        username = entry_name.get().strip()
        if not username: return
        if messagebox.askyesno("Confirmar", f"Eliminar {username}?"):
            if pdb.delete_password(username) > 0:
                refresh_list()
                entry_name.delete(0, tk.END)
                entry_password.delete(0, tk.END)
                update_entropy()
            else:
                messagebox.showwarning("Erro", "Não encontrado.")

    # --- Botões Principais ---
    frame_btns = tk.Frame(frame_right)
    frame_btns.grid(row=4, column=0, columnspan=3, pady=20)
    tk.Button(frame_btns, text="Guardar / Atualizar", command=add_or_update, bg="#ddffdd", width=20).pack(side="left", padx=5)
    tk.Button(frame_btns, text="Eliminar", command=delete_entry, bg="#ffdddd", width=15).pack(side="left", padx=5)

    listbox_sites.bind("<<ListboxSelect>>", show_selected)

    # ================= NOVO: Botão Sair =================
    # Usamos o método .place() para fixar no canto inferior direito
    # relx=1.0, rely=1.0 indica 100% da largura e altura (o canto)
    # anchor="se" (South East) alinha o canto do botão com esse ponto
    btn_exit = tk.Button(app, text="Sair", command=app.destroy, bg="#e0e0e0", width=10)
    btn_exit.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

    refresh_list()
    app.mainloop()

if __name__ == "__main__":
    start_menu()