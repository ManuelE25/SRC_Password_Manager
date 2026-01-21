# app.py
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog, ttk
import secrets
import string
import math
import time
import pyperclip  # pip install pyperclip

from storage import PasswordDatabase, InvalidPasswordException

# ================= Lógica Matemática =================

def calculate_entropy(password: str) -> float:
    if not password: return 0
    pool_size = 0
    if any(c.islower() for c in password): pool_size += 26
    if any(c.isupper() for c in password): pool_size += 26
    if any(c.isdigit() for c in password): pool_size += 10
    if any(c in string.punctuation for c in password): pool_size += 32
    if pool_size == 0: return 0
    return len(password) * math.log2(pool_size)

def generate_strong_password(length=16, use_upper=True, use_digits=True, use_symbols=True) -> str:
    chars = string.ascii_lowercase
    if use_upper: chars += string.ascii_uppercase
    if use_digits: chars += string.digits
    if use_symbols: chars += string.punctuation
    if not chars: return ""
    return ''.join(secrets.choice(chars) for _ in range(length))

# ================= Diálogos Auxiliares =================

def ask_master_password(prompt: str) -> str:
    root = tk.Tk()
    root.withdraw()
    pw = simpledialog.askstring("Segurança", prompt, show="*")
    root.destroy()
    return pw

def ask_new_db_config(title: str):
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
            messagebox.showerror("Erro", "Password vazia.", parent=dialog)
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
        pw = generate_strong_password(var_len.get(), var_upper.get(), var_digits.get(), var_symbols.get())
        generated_pw.set(pw)

    def accept():
        top.destroy()
        
    tk.Button(top, text="Gerar Nova", command=run_generate).pack(pady=2)
    tk.Button(top, text="Usar esta Password", command=accept, bg="#ddffdd", height=2).pack(pady=10)
    run_generate()
    parent.wait_window(top)
    return generated_pw.get()

# ================= Menus de Entrada =================

def start_menu():
    root = tk.Tk()
    root.title("Gestor Seguro")
    root.geometry("360x200")
    root.resizable(False, False)
    action_var = tk.StringVar(value="open")

    def choose_action():
        choice = action_var.get()
        root.destroy()
        if choice == "open": open_database()
        else: create_database()

    tk.Label(root, text="Gestor de Passwords", font=("Arial", 14, "bold")).pack(pady=15)
    frame_opts = tk.Frame(root)
    frame_opts.pack(pady=5)
    tk.Radiobutton(frame_opts, text="Abrir cofre existente", variable=action_var, value="open").pack(anchor="w")
    tk.Radiobutton(frame_opts, text="Criar novo cofre", variable=action_var, value="create").pack(anchor="w")
    tk.Button(root, text="Continuar", command=choose_action, width=20).pack(pady=20)
    root.mainloop()

def open_database():
    db_path = filedialog.askopenfilename(title="Abrir cofre", filetypes=[("Cofre", "*.db")])
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
    except Exception as e:
        messagebox.showerror("Erro", f"Acesso negado ou erro: {e}")
        start_menu()

def create_database():
    db_path = filedialog.asksaveasfilename(title="Guardar cofre", defaultextension=".db", filetypes=[("Cofre", "*.db")])
    if not db_path:
        start_menu()
        return
    password, algo = ask_new_db_config("Novo Cofre")
    if not password:
        start_menu()
        return
    pdb = PasswordDatabase(db_path)
    try:
        pdb.create_new(password, algo=algo)
        launch_app(pdb)
    except Exception as e:
        messagebox.showerror("Erro", str(e))
        start_menu()

# ================= Aplicação Principal =================

def launch_app(pdb: PasswordDatabase):
    app = tk.Tk()
    app.geometry("1000x550") 
    app.title(f"Cofre Digital - {pdb.encryption_algo.upper()}")

    selected_old_title = None

    # Estilos
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Red.Horizontal.TProgressbar", foreground='red', background='red')
    style.configure("Yellow.Horizontal.TProgressbar", foreground='#FFAA00', background='#FFAA00')
    style.configure("Green.Horizontal.TProgressbar", foreground='green', background='green')
    
    # Estilo Treeview (Árvore)
    style.configure("Treeview", font=('Arial', 10), rowheight=25)
    style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))

    # Timeout
    last_activity = time.time()
    LOCK_TIMEOUT = 300 
    def reset_timer(event):
        nonlocal last_activity
        last_activity = time.time()
    def check_inactivity():
        if time.time() - last_activity > LOCK_TIMEOUT:
            app.destroy()
            messagebox.showinfo("Bloqueado", "Tempo esgotado.")
            start_menu()
        else:
            app.after(1000, check_inactivity)
    app.bind_all("<Any-KeyPress>", reset_timer)
    app.bind_all("<Any-Button>", reset_timer)
    app.after(1000, check_inactivity)

    # --- Layout Esquerdo (Árvore de Pastas) ---
    frame_left = tk.Frame(app)
    frame_left.grid(row=0, column=0, rowspan=4, padx=15, pady=15, sticky="nsew") 
    
    # Configuração de pesos para a janela redimensionar bem
    app.grid_columnconfigure(0, weight=1)
    app.grid_columnconfigure(1, weight=2)
    app.grid_rowconfigure(0, weight=1)

    tk.Label(frame_left, text="As Minhas Pastas", font=("Arial", 10, "bold")).pack(anchor="w")
    
    # Treeview
    tree = ttk.Treeview(frame_left, columns=("type"), show="tree", selectmode="browse")
    tree.pack(side="left", fill="both", expand=True)
    
    scrollbar = tk.Scrollbar(frame_left, orient="vertical", command=tree.yview)
    scrollbar.pack(side="right", fill="y")
    tree.config(yscrollcommand=scrollbar.set)

    # --- Layout Direito (Formulário) ---
    frame_right = tk.Frame(app)
    frame_right.grid(row=0, column=1, padx=20, pady=15, sticky="n")

    def create_row(label_text, row):
        tk.Label(frame_right, text=label_text).grid(row=row, column=0, padx=5, pady=5, sticky="e")
        if label_text == "Pasta / Categoria:":
            # Combobox para as pastas
            entry = ttk.Combobox(frame_right, width=43)
        else:
            entry = tk.Entry(frame_right, width=45)
        entry.grid(row=row, column=1, padx=5, pady=5)
        return entry

    # Campos
    entry_folder = create_row("Pasta / Categoria:", 0) 
    entry_title = create_row("Título (Único):", 1)
    entry_url = create_row("URL:", 2)
    entry_user = create_row("Utilizador:", 3)
    
    tk.Label(frame_right, text="Password:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
    entry_password = tk.Entry(frame_right, width=45, show="*")
    entry_password.grid(row=4, column=1, padx=5, pady=5)

    lbl_entropy = tk.Label(frame_right, text="Força: N/A", font=("Arial", 8))
    lbl_entropy.grid(row=5, column=1, sticky="w", padx=5)
    progress = ttk.Progressbar(frame_right, orient="horizontal", length=275, mode="determinate")
    progress.grid(row=6, column=1, sticky="w", padx=5, pady=(0, 10))

    def update_entropy(event=None):
        pwd = entry_password.get()
        bits = calculate_entropy(pwd)
        progress["value"] = min(bits, 100)
        if bits < 40:
            progress.config(style="Red.Horizontal.TProgressbar")
            lbl_entropy.config(text=f"Fraca ({int(bits)} bits)", fg="red")
        elif bits < 80:
            progress.config(style="Yellow.Horizontal.TProgressbar")
            lbl_entropy.config(text=f"Média ({int(bits)} bits)", fg="#FFAA00")
        else:
            progress.config(style="Green.Horizontal.TProgressbar")
            lbl_entropy.config(text=f"Forte ({int(bits)} bits)", fg="green")
    entry_password.bind("<KeyRelease>", update_entropy)

    frame_tools = tk.Frame(frame_right)
    frame_tools.grid(row=4, column=2, padx=5, sticky="w")
    
    def toggle_pw():
        entry_password.config(show='' if entry_password.cget('show') == '*' else '*')
    tk.Button(frame_tools, text="👁", command=toggle_pw, width=3).pack(side="left", padx=1)

    def gen_pw():
        pw = open_generator_dialog(app)
        if pw:
            entry_password.delete(0, tk.END)
            entry_password.insert(0, pw)
            update_entropy()
    tk.Button(frame_tools, text="⚙", command=gen_pw, width=3).pack(side="left", padx=1)

    def copy_pw():
        pw = entry_password.get()
        if pw:
            pyperclip.copy(pw)
            messagebox.showinfo("Info", "Password copiada (30s limpa).")
            app.after(30000, lambda: pyperclip.copy("") if pyperclip.paste() == pw else None)
    tk.Button(frame_tools, text="📋", command=copy_pw, width=3).pack(side="left", padx=1)

    # --- Lógica CRUD ---

    def clear_form():
        nonlocal selected_old_title
        selected_old_title = None
        entry_folder.set('')
        entry_title.delete(0, tk.END)
        entry_url.delete(0, tk.END)
        entry_user.delete(0, tk.END)
        entry_password.delete(0, tk.END)
        update_entropy()
        
        # Remove seleção visual da árvore
        for item in tree.selection():
            tree.selection_remove(item)

    def refresh_list():
        # Limpar árvore visual
        for item in tree.get_children():
            tree.delete(item)
            
        # Obter dados
        entries = pdb.list_entries()
        
        # Atualizar a Combobox com pastas existentes
        existing_folders = pdb.get_all_folders()
        entry_folder['values'] = existing_folders
        
        # Dicionário para gerir IDs das pastas na Treeview
        folder_nodes = {}
        
        # Nó para "Geral" (Sem pasta)
        root_general = tree.insert("", "end", text="Geral / Sem Pasta", open=True)
        
        for item in entries:
            folder = item["folder"]
            title = item["title"]
            
            # Determinar quem é o pai deste item
            if folder:
                if folder not in folder_nodes:
                    # Cria o nó da pasta se não existe
                    folder_id = tree.insert("", "end", text=folder, open=True)
                    folder_nodes[folder] = folder_id
                parent_id = folder_nodes[folder]
            else:
                parent_id = root_general
            
            # Adiciona o Item como FILHO da Pasta
            # 'values=("entry")' serve para distinguirmos que é um item e não uma pasta
            tree.insert(parent_id, "end", text=title, values=("entry"))

    def on_add():
        """Adicionar novo item."""
        folder = entry_folder.get().strip()
        title = entry_title.get().strip()
        url = entry_url.get().strip()
        user = entry_user.get().strip()
        pw = entry_password.get()
        
        if not title or not pw:
            messagebox.showwarning("Faltam dados", "Título e Password são obrigatórios.")
            return

        if pdb.get_entry_by_title(title) is not None:
            messagebox.showerror("Erro", f"O título '{title}' já existe.\nUse outro nome.")
            return

        try:
            pdb.add_entry(folder, title, url, user, pw)
            messagebox.showinfo("Sucesso", "Adicionado.")
            refresh_list()
            clear_form()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def on_update():
        """Atualizar item existente."""
        nonlocal selected_old_title
        if selected_old_title is None:
            messagebox.showwarning("Aviso", "Selecione um item (filho de uma pasta) para editar.")
            return

        new_folder = entry_folder.get().strip()
        new_title = entry_title.get().strip()
        url = entry_url.get().strip()
        user = entry_user.get().strip()
        pw = entry_password.get()

        if not new_title or not pw:
            messagebox.showwarning("Erro", "Título e Password são obrigatórios.")
            return

        # Verificar colisão de nomes se o título mudou
        if new_title != selected_old_title:
            if pdb.get_entry_by_title(new_title) is not None:
                messagebox.showerror("Erro", f"Já existe outro item com o nome '{new_title}'.")
                return

        try:
            # Apaga o antigo, cria o novo
            pdb.delete_entry(selected_old_title)
            pdb.add_entry(new_folder, new_title, url, user, pw)
            messagebox.showinfo("Sucesso", "Atualizado.")
            refresh_list()
            clear_form()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def on_delete():
        title = entry_title.get().strip()
        if not title: return

        target = selected_old_title if selected_old_title else title
        
        if messagebox.askyesno("Apagar", f"Eliminar '{target}'?"):
            pdb.delete_entry(target)
            refresh_list()
            clear_form()

    def on_tree_select(event):
        """Carrega dados para o form ao clicar na árvore."""
        nonlocal selected_old_title
        
        selected_items = tree.selection()
        if not selected_items: return
        
        item_id = selected_items[0]
        item_text = tree.item(item_id, "text")
        item_values = tree.item(item_id, "values")
        
        # Verificar se é item ou pasta
        is_entry = False
        if item_values and item_values[0] == "entry":
            is_entry = True
            
        if not is_entry:
            # Clicou numa pasta -> limpa o form
            clear_form()
            return

        # Clicou num item válido
        title = item_text
        data = pdb.get_entry_by_title(title)
        
        if data:
            selected_old_title = data["title"]
            
            entry_folder.set(data["folder"])
            
            entry_title.delete(0, tk.END)
            entry_title.insert(0, data["title"])
            
            entry_url.delete(0, tk.END)
            entry_url.insert(0, data["url"])
            
            entry_user.delete(0, tk.END)
            entry_user.insert(0, data["username"])
            
            entry_password.delete(0, tk.END)
            entry_password.insert(0, data["password"])
            update_entropy()

    tree.bind("<<TreeviewSelect>>", on_tree_select)

    # --- Botões ---
    frame_btns = tk.Frame(frame_right)
    frame_btns.grid(row=7, column=0, columnspan=3, pady=25)

    tk.Button(frame_btns, text="Adicionar", command=on_add, bg="#ddffdd", width=12).pack(side="left", padx=5)
    tk.Button(frame_btns, text="Atualizar", command=on_update, bg="#fffddd", width=12).pack(side="left", padx=5)
    tk.Button(frame_btns, text="Limpar", command=clear_form, width=8).pack(side="left", padx=5)
    tk.Button(frame_btns, text="Eliminar", command=on_delete, bg="#ffdddd", width=10).pack(side="left", padx=15)

    btn_exit = tk.Button(app, text="Sair", command=app.destroy, bg="#e0e0e0", width=10)
    btn_exit.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

    refresh_list()
    app.mainloop()

if __name__ == "__main__":
    start_menu()