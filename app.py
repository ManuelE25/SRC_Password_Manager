# app.py
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog, ttk
import secrets
import string
import math
import time
import pyperclip  # pip install pyperclip
import random     # Necessário para o teclado virtual

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

# ================= Teclado Virtual Anti-Keylogger =================

def open_virtual_keyboard(parent, target_entry, on_key_press=None):
    vk = tk.Toplevel(parent)
    vk.title("Teclado Seguro")
    vk.geometry("550x330")
    vk.resizable(False, False)
    vk.attributes('-topmost', True) 

    lbl_preview = tk.Label(vk, text="Inserção Segura...", font=("Arial", 10, "italic"), fg="gray")
    lbl_preview.pack(pady=5)

    keys_lower = list(string.ascii_lowercase)
    keys_upper = list(string.ascii_uppercase)
    keys_digits = list(string.digits)
    keys_symbols = list("!@#$%^&*()_+-=[]{}|;:,.<>?/")

    current_keys = keys_lower + keys_digits 
    is_shifted = False

    frame_keys = tk.Frame(vk)
    frame_keys.pack(pady=10, padx=10)

    def insert_char(char):
        target_entry.insert(tk.END, char)
        lbl_preview.config(text=f"Inserido: (Protegido)", fg="green")
        if on_key_press:
            on_key_press()

    def refresh_layout():
        for widget in frame_keys.winfo_children():
            widget.destroy()

        row = 0
        col = 0
        max_cols = 12

        for char in current_keys:
            btn = tk.Button(frame_keys, text=char, width=4, height=2, 
                            command=lambda c=char: insert_char(c))
            btn.grid(row=row, column=col, padx=2, pady=2)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def toggle_shift():
        nonlocal is_shifted, current_keys
        is_shifted = not is_shifted
        if is_shifted:
            current_keys = keys_upper + keys_symbols
            btn_shift.config(bg="#aaccff", relief="sunken")
        else:
            current_keys = keys_lower + keys_digits
            btn_shift.config(bg="#f0f0f0", relief="raised")
        refresh_layout()

    def shuffle_keys():
        random.shuffle(current_keys)
        refresh_layout()

    def backspace():
        current_pos = target_entry.index(tk.INSERT)
        if current_pos > 0:
            target_entry.delete(current_pos - 1)
            if on_key_press:
                on_key_press()

    frame_controls = tk.Frame(vk)
    frame_controls.pack(fill="x", side="bottom", pady=10, padx=10)

    btn_shift = tk.Button(frame_controls, text="SHIFT / Símbolos", command=toggle_shift, height=2, width=15)
    btn_shift.pack(side="left", padx=5)

    tk.Button(frame_controls, text="🔀 Baralhar", command=shuffle_keys, height=2, width=10).pack(side="left", padx=5)
    tk.Button(frame_controls, text="⌫ Apagar", command=backspace, height=2, width=10, bg="#ffdddd").pack(side="left", padx=5)
    tk.Button(frame_controls, text="Fechar", command=vk.destroy, height=2, width=10).pack(side="right", padx=5)

    refresh_layout()

# ================= Diálogos Auxiliares =================

def ask_master_password(prompt: str) -> str:
    dialog = tk.Tk()
    dialog.title("Segurança")
    dialog.geometry("400x180")
    dialog.resizable(False, False)
    
    result = {"pw": None}

    tk.Label(dialog, text=prompt, wraplength=350).pack(pady=15)
    
    frame_entry = tk.Frame(dialog)
    frame_entry.pack(pady=5)
    
    entry = tk.Entry(frame_entry, show="*", width=30)
    entry.pack(side="left", padx=5)
    
    tk.Button(frame_entry, text="⌨", command=lambda: open_virtual_keyboard(dialog, entry)).pack(side="left")
    
    def on_ok():
        result["pw"] = entry.get()
        dialog.destroy()
        
    def on_cancel():
        dialog.destroy()

    frame_btns = tk.Frame(dialog)
    frame_btns.pack(pady=15)
    tk.Button(frame_btns, text="OK", command=on_ok, width=10, bg="#ddffdd").pack(side="left", padx=10)
    tk.Button(frame_btns, text="Cancelar", command=on_cancel, width=10).pack(side="left", padx=10)

    dialog.bind('<Return>', lambda e: on_ok())
    entry.focus_set()
    dialog.mainloop()
    
    return result["pw"]

def ask_new_db_config(title: str):
    dialog = tk.Tk()
    dialog.title(title)
    dialog.geometry("350x250")
    dialog.resizable(False, False)
    
    result = {"password": None, "algo": "aes-gcm"}
    
    tk.Label(dialog, text="Password Mestra:").pack(pady=(15, 5))
    
    frame_pw = tk.Frame(dialog)
    frame_pw.pack(pady=5)
    entry_pw = tk.Entry(frame_pw, show="*", width=25)
    entry_pw.pack(side="left", padx=2)
    tk.Button(frame_pw, text="⌨", command=lambda: open_virtual_keyboard(dialog, entry_pw)).pack(side="left")
    
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

    # --- Layout Esquerdo ---
    frame_left = tk.Frame(app)
    frame_left.grid(row=0, column=0, rowspan=4, padx=15, pady=15, sticky="nsew") 
    
    app.grid_columnconfigure(0, weight=1)
    app.grid_columnconfigure(1, weight=2)
    app.grid_rowconfigure(0, weight=1)

    # Pesquisa
    frame_search = tk.Frame(frame_left)
    frame_search.pack(fill="x", pady=(0, 10))
    tk.Label(frame_search, text="🔍").pack(side="left")
    entry_search = tk.Entry(frame_search)
    entry_search.pack(side="left", fill="x", expand=True, padx=5)

    tk.Label(frame_left, text="As Minhas Pastas", font=("Arial", 10, "bold")).pack(anchor="w")
    
    # Treeview
    tree = ttk.Treeview(frame_left, columns=("type"), show="tree", selectmode="browse")
    # Agora usamos side="top" para deixar espaço em baixo para o botão de auditoria
    tree.pack(side="top", fill="both", expand=True)
    
    scrollbar = tk.Scrollbar(frame_left, orient="vertical", command=tree.yview)
    scrollbar.pack(side="right", fill="y", before=tree) # 'before' garante que fica ao lado da tree
    tree.config(yscrollcommand=scrollbar.set)

    # --- Layout Direito ---
    frame_right = tk.Frame(app)
    frame_right.grid(row=0, column=1, padx=20, pady=15, sticky="n")

    def create_row(label_text, row):
        tk.Label(frame_right, text=label_text).grid(row=row, column=0, padx=5, pady=5, sticky="e")
        if label_text == "Pasta / Categoria:":
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

    # --- Barra de Ferramentas do lado Direito ---
    frame_tools = tk.Frame(frame_right)
    frame_tools.grid(row=4, column=2, padx=5, sticky="w")
    
    # 1. Mostrar/Esconder
    def toggle_pw():
        entry_password.config(show='' if entry_password.cget('show') == '*' else '*')
    tk.Button(frame_tools, text="👁", command=toggle_pw, width=3).pack(side="left", padx=1)

    # 2. Gerar
    def gen_pw():
        pw = open_generator_dialog(app)
        if pw:
            entry_password.delete(0, tk.END)
            entry_password.insert(0, pw)
            update_entropy()
    tk.Button(frame_tools, text="⚙", command=gen_pw, width=3).pack(side="left", padx=1)

    # 3. Teclado Virtual
    def open_kb():
        open_virtual_keyboard(app, entry_password, on_key_press=lambda: update_entropy())
    tk.Button(frame_tools, text="⌨", command=open_kb, width=3).pack(side="left", padx=1)

    # 4. Copiar
    def copy_pw():
        pw = entry_password.get()
        if pw:
            pyperclip.copy(pw)
            messagebox.showinfo("Info", "Password copiada (30s limpa).")
            app.after(30000, lambda: pyperclip.copy("") if pyperclip.paste() == pw else None)
    tk.Button(frame_tools, text="📋", command=copy_pw, width=3).pack(side="left", padx=1)

    # ================= FUNCIONALIDADE: AUDITORIA EM JANELA NOVA =================
    
    def load_item_by_title(title):
        data = pdb.get_entry_by_title(title)
        if data:
            nonlocal selected_old_title
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

    def open_audit_window():
        audit_win = tk.Toplevel(app)
        audit_win.title("Auditoria de Reutilização de Passwords")
        audit_win.geometry("600x400")
        
        tk.Label(audit_win, text="Contas com a mesma Password:", font=("Arial", 12, "bold"), fg="#d9534f").pack(pady=10)
        tk.Label(audit_win, text="(Duplo clique num registo para editar)", font=("Arial", 9, "italic")).pack()

        # Treeview para a auditoria
        cols = ("Username", "Pasta")
        audit_tree = ttk.Treeview(audit_win, columns=cols, show="tree headings")
        audit_tree.heading("#0", text="Grupos de Risco")
        audit_tree.heading("Username", text="Utilizador")
        audit_tree.heading("Pasta", text="Pasta")
        audit_tree.column("#0", width=250)
        
        audit_tree.pack(fill="both", expand=True, padx=10, pady=10)

        entries = pdb.list_entries()
        pass_map = {} 

        for item in entries:
            pwd = item['password']
            if not pwd: continue
            if pwd in pass_map:
                pass_map[pwd].append(item)
            else:
                pass_map[pwd] = [item]
        
        reused_count = 0
        group_idx = 1
        
        for pwd, items in pass_map.items():
            if len(items) > 1:
                reused_count += 1
                # NÓ PAI GENÉRICO (SEM PASSWORD)
                display_text = f"⚠️ Grupo de Risco #{group_idx} ({len(items)} contas)"
                parent_id = audit_tree.insert("", "end", text=display_text, open=True)
                group_idx += 1
                
                for item in items:
                    audit_tree.insert(parent_id, "end", text=item['title'], values=(item['username'], item['folder']), tags=(item['title'],))

        if reused_count == 0:
            tk.Label(audit_win, text="Excelente! Nenhuma reutilização encontrada.", fg="green").pack()
        
        def on_audit_double_click(event):
            item_id = audit_tree.selection()[0]
            vals = audit_tree.item(item_id, "values")
            if vals:
                title_to_load = audit_tree.item(item_id, "text")
                load_item_by_title(title_to_load)
                audit_win.destroy()
                messagebox.showinfo("Editar", f"Carregado: {title_to_load}\nAltere a password agora.")

        audit_tree.bind("<Double-1>", on_audit_double_click)

    # --- BOTÃO DE AUDITORIA NO FUNDO DO FRAME ESQUERDO ---
    frame_audit_btn = tk.Frame(frame_left)
    frame_audit_btn.pack(side="bottom", fill="x", padx=10, pady=10)
    
    tk.Button(frame_audit_btn, text="♻ Verificar Passwords Repetidas", command=open_audit_window, bg="#ffebcd").pack(fill="x")

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
        for item in tree.selection():
            tree.selection_remove(item)

    def refresh_list(search_query=""):
        for item in tree.get_children():
            tree.delete(item)
            
        entries = pdb.list_entries()
        existing_folders = pdb.get_all_folders()
        entry_folder['values'] = existing_folders

        if search_query:
            query = search_query.lower()
            for item in entries:
                title = item["title"]
                folder = item["folder"]
                if (query in title.lower()) or (query in folder.lower()) or (query in item["username"].lower()):
                    display_text = f"{title}   [{folder if folder else 'Geral'}]"
                    tree.insert("", "end", text=display_text, values=("entry", title)) 
            return
        
        folder_nodes = {}
        root_general = tree.insert("", "end", text="Geral / Sem Pasta", open=True)
        
        for item in entries:
            folder = item["folder"]
            title = item["title"]
            
            if folder:
                if folder not in folder_nodes:
                    folder_id = tree.insert("", "end", text=folder, open=True)
                    folder_nodes[folder] = folder_id
                parent_id = folder_nodes[folder]
            else:
                parent_id = root_general
            
            tree.insert(parent_id, "end", text=title, values=("entry", title))

    def on_search(event):
        query = entry_search.get().strip()
        refresh_list(query)
    entry_search.bind("<KeyRelease>", on_search)

    def on_add():
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
            entry_search.delete(0, tk.END)
            refresh_list()
            clear_form()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def on_update():
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

        if new_title != selected_old_title:
            if pdb.get_entry_by_title(new_title) is not None:
                messagebox.showerror("Erro", f"Já existe outro item com o nome '{new_title}'.")
                return

        try:
            pdb.delete_entry(selected_old_title)
            pdb.add_entry(new_folder, new_title, url, user, pw)
            messagebox.showinfo("Sucesso", "Atualizado.")
            entry_search.delete(0, tk.END)
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
            entry_search.delete(0, tk.END)
            refresh_list()
            clear_form()

    def on_tree_select(event):
        nonlocal selected_old_title
        selected_items = tree.selection()
        if not selected_items: return
        item_id = selected_items[0]
        item_values = tree.item(item_id, "values")
        
        if not (item_values and item_values[0] == "entry"):
            clear_form()
            return

        real_title = item_values[1]
        data = pdb.get_entry_by_title(real_title)
        
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