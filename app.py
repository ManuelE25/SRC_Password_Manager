import tkinter as tk
from tkinter import messagebox, filedialog, ttk, simpledialog
import string
import secrets
import math
import random
import time
import pyperclip  # pip install pyperclip

import storage

APP_ESTADO = {
    "root": None,          # Janela principal
    "ultimo_toque": 0,     # Para o timeout de inatividade
    "id_selecionado": None,# Qual password estamos a editar
    "titulo_antigo": None  # Para saber se mudou o nome
}

WIDGETS = {}

# ================= 1. Matemática e Lógica =================

def calcular_entropia(password):
    if not password: return 0
    tamanho = len(password)
    pool = 0
    if any(c.islower() for c in password): pool += 26
    if any(c.isupper() for c in password): pool += 26
    if any(c.isdigit() for c in password): pool += 10
    if any(c in string.punctuation for c in password): pool += 32
    
    if pool == 0: return 0
    return tamanho * math.log2(pool)

def gerar_password_avancada(tamanho, usar_lower, usar_upper, usar_digits, usar_symbols):
    chars = ""
    if usar_lower: chars += string.ascii_lowercase
    if usar_upper: chars += string.ascii_uppercase
    if usar_digits: chars += string.digits
    if usar_symbols: chars += string.punctuation
    
    if not chars: return "Selecione pelo menos um tipo!"
    return ''.join(secrets.choice(chars) for _ in range(int(tamanho)))
# ================= 2. Janelas Especiais (Funcionalidades) =================

def abrir_gerador_passwords():
    # Janela flutuante para configurar a geração
    win = tk.Toplevel(APP_ESTADO["root"])
    win.title("Gerador Avançado")
    win.geometry("380x350")
    
    # --- CORREÇÃO AQUI ---
    # Adicionámos "master=win" a todas as variáveis para fixar o erro
    v_tamanho = tk.IntVar(master=win, value=16)
    v_lower = tk.BooleanVar(master=win, value=True)
    v_upper = tk.BooleanVar(master=win, value=True)
    v_num = tk.BooleanVar(master=win, value=True)
    v_sym = tk.BooleanVar(master=win, value=True)
    v_resultado = tk.StringVar(master=win)
    # ---------------------

    # Função interna para gerar (chamada pelos botões)
    def gerar(evento_ignore=None):
        password = gerar_password_avancada(
            v_tamanho.get(), 
            v_lower.get(),
            v_upper.get(), 
            v_num.get(), 
            v_sym.get()
        )
        v_resultado.set(password)

    # --- Interface ---
    tk.Label(win, text="Comprimento:").pack(pady=(10, 0))
    
    tk.Scale(win, from_=4, to=64, orient="horizontal", variable=v_tamanho, length=250, command=gerar).pack()
    
    frame_opts = tk.Frame(win)
    frame_opts.pack(pady=10)
    
    tk.Checkbutton(frame_opts, text="a-z (Minúsculas)", variable=v_lower, command=gerar).pack(anchor="w")
    tk.Checkbutton(frame_opts, text="A-Z (Maiúsculas)", variable=v_upper, command=gerar).pack(anchor="w")
    tk.Checkbutton(frame_opts, text="0-9 (Números)", variable=v_num, command=gerar).pack(anchor="w")
    tk.Checkbutton(frame_opts, text="!@# (Símbolos)", variable=v_sym, command=gerar).pack(anchor="w")

    entry_res = tk.Entry(win, textvariable=v_resultado, justify="center", font=("Consolas", 12), bg="#f0f0f0")
    entry_res.pack(pady=10, fill="x", padx=20)

    def usar():
        WIDGETS["password"].delete(0, tk.END)
        WIDGETS["password"].insert(0, v_resultado.get())
        atualizar_barra_entropia_da_password() 
        win.destroy()

    frame_btns = tk.Frame(win)
    frame_btns.pack(pady=10)
    
    tk.Button(frame_btns, text="🔄 Regenerar", command=gerar).pack(side="left", padx=5)
    tk.Button(frame_btns, text="✅ Usar Esta password", command=usar, bg="#ddffdd", height=2).pack(side="left", padx=5)
    
    gerar()
def abrir_teclado_virtual(entry_alvo):
    win = tk.Toplevel(APP_ESTADO["root"])
    win.title("Teclado Seguro")
    win.geometry("600x350")
    win.attributes('-topmost', True)
    
    lbl_info = tk.Label(win, text="Inserção Segura...", fg="gray")
    lbl_info.pack(pady=5)
    
    frame_teclas = tk.Frame(win)
    frame_teclas.pack(pady=10)

  
    teclas_normais = string.ascii_lowercase + string.digits
    teclas_shift   = string.ascii_uppercase + string.punctuation
    
    estado = {"shift": False}

    def desenhar_teclas():
        for b in frame_teclas.winfo_children(): b.destroy()
        

        caracteres_atuais = teclas_shift if estado["shift"] else teclas_normais

        for i, letra in enumerate(caracteres_atuais):
            tk.Button(frame_teclas, text=letra, width=5, height=2, 
                      command=lambda x=letra: inserir(x)).grid(row=i//12, column=i%12, padx=2, pady=2)

    def inserir(char):
        entry_alvo.insert(tk.END, char)
        lbl_info.config(text="Inserido (Protegido)", fg="green")
        atualizar_barra_entropia_da_password()

    def alternar_shift():
        estado["shift"] = not estado["shift"]
        desenhar_teclas()

    def apagar_ultimo():

            posicao_atual = entry_alvo.index(tk.INSERT)
            if posicao_atual > 0:
                entry_alvo.delete(posicao_atual - 1)
                atualizar_barra_entropia_da_password()

    # Botões de controle
    frame_ctrl = tk.Frame(win)
    frame_ctrl.pack(side="bottom", pady=10)
    
    tk.Button(frame_ctrl, text="SHIFT / Símbolos", command=alternar_shift, width=15, height=2).pack(side="left", padx=5)
    tk.Button(frame_ctrl, text="Apagar", command=apagar_ultimo, bg="#ffdddd", width=10, height=2).pack(side="left", padx=5)
    
    desenhar_teclas()

def abrir_auditoria():
    win = tk.Toplevel(APP_ESTADO["root"])
    win.title("Auditoria: passwords Repetidas")
    win.geometry("600x400")
    
    tk.Label(win, text="Contas com a mesma password:", font=("Arial", 12, "bold"), fg="red").pack(pady=10)
    
    tree_audit = ttk.Treeview(win, columns=("user", "folder"), show="tree headings")
    tree_audit.heading("#0", text="Grupos de Risco")
    tree_audit.heading("user", text="Utilizador")
    tree_audit.heading("folder", text="Pasta")
    tree_audit.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Lógica de agrupamento
    todas = storage.ler_todas_passwords()
    mapa_passwords = {} # Dicionario: password -> lista de contas
    
    for item in todas:
        password = item['password']
        if not password: continue
        if password not in mapa_passwords: mapa_passwords[password] = []
        mapa_passwords[password].append(item)
        
    encontrou_problema = False
    for password, lista in mapa_passwords.items():
        if len(lista) > 1:
            encontrou_problema = True
            texto_grupo = f"{len(lista)} contas com a mesma password"
            pai = tree_audit.insert("", "end", text=texto_grupo, open=True)
            for item in lista:
                tree_audit.insert(pai, "end", text=item['titulo'], values=(item['utilizador'], item['pasta']))
                
    if not encontrou_problema:
        tk.Label(win, text="Não existem passwords repetidas", fg="green").pack()

# ================= 3. Funções da Interface Principal =================

def verificar_inatividade():
    # Verifica se a janela ainda existe antes de continuar
    if not APP_ESTADO["root"] or not APP_ESTADO["root"].winfo_exists():
        return

    agora = time.time()
    if agora - APP_ESTADO["ultimo_toque"] > 300: 
        APP_ESTADO["root"].destroy()
        messagebox.showinfo("Bloqueado", "Tempo esgotado por segurança.")
        menu_inicial()
    else:
        # Só agenda o próximo se a janela ainda existir
        try:
            APP_ESTADO["root"].after(1000, verificar_inatividade)
        except:
            pass

def resetar_timer(event):
    APP_ESTADO["ultimo_toque"] = time.time()

def atualizar_barra_entropia_da_password(event=None):
    password = WIDGETS["password"].get()
    bits = calcular_entropia(password)
    
    # Define cor e texto
    if bits < 40:
        estilo = "Red.Horizontal.TProgressbar"
        texto = f"Fraca ({int(bits)} bits)"
        cor_texto = "red"
    elif bits < 80:
        estilo = "Yellow.Horizontal.TProgressbar"
        texto = f"Média ({int(bits)} bits)"
        cor_texto = "#FFAA00"
    else:
        estilo = "Green.Horizontal.TProgressbar"
        texto = f"Forte ({int(bits)} bits)"
        cor_texto = "green"
        
    WIDGETS["progress"].config(style=estilo)
    WIDGETS["progress"]["value"] = min(bits, 100)
    WIDGETS["lbl_forca"].config(text=texto, fg=cor_texto)

def copiar_password():
    password = WIDGETS["password"].get()
    if password:
        pyperclip.copy(password)
        messagebox.showinfo("Clipboard", "password copiada! Será limpa em 30s.")
        # Limpa o clipboard daqui a 30s
        APP_ESTADO["root"].after(30000, lambda: pyperclip.copy("") if pyperclip.paste() == password else None)

def toggle_ver_password():
    atual = WIDGETS["password"].cget('show')
    novo = '' if atual == '*' else '*'
    WIDGETS["password"].config(show=novo)

# --- CRUD (Criar, Ler, Atualizar, Apagar) ---

def limpar_formulario():
    APP_ESTADO["id_selecionado"] = None
    APP_ESTADO["titulo_antigo"] = None
    
    WIDGETS["folder"].set('')
    WIDGETS["title"].delete(0, tk.END)
    WIDGETS["url"].delete(0, tk.END)
    WIDGETS["user"].delete(0, tk.END)
    WIDGETS["password"].delete(0, tk.END)
    
    WIDGETS["tree"].selection_remove(WIDGETS["tree"].selection())
    atualizar_barra_entropia_da_password()

def preencher_formulario(item_db):
    limpar_formulario()
    APP_ESTADO["id_selecionado"] = item_db["id"]
    APP_ESTADO["titulo_antigo"] = item_db["titulo"]
    
    WIDGETS["folder"].set(item_db["pasta"])
    WIDGETS["title"].insert(0, item_db["titulo"])
    WIDGETS["url"].insert(0, item_db["url"])
    WIDGETS["user"].insert(0, item_db["utilizador"])
    WIDGETS["password"].insert(0, item_db["password"])
    atualizar_barra_entropia_da_password()

def atualizar_lista(pesquisa=""):
    tree = WIDGETS["tree"]
    # Limpa visualmente
    for i in tree.get_children(): tree.delete(i)
    
    dados = storage.ler_todas_passwords()
    
    # Atualiza lista de pastas no Combobox
    pastas = sorted(list(set([d['pasta'] for d in dados if d['pasta']])))
    WIDGETS["folder"]['values'] = pastas

    if pesquisa:
        # Modo Pesquisa (Lista plana)
        p = pesquisa.lower()
        for d in dados:
            if p in d['titulo'].lower() or p in d['utilizador'].lower() or p in d['pasta'].lower():
                texto = f"{d['titulo']}   [{d['pasta'] or 'Geral'}]"
                tree.insert("", "end", text=texto, values=("entry", d['id']))
    else:
        # Modo Pastas (Hierarquia)
        nos_pasta = {}
        raiz_geral = tree.insert("", "end", text="Geral / Sem Pasta", open=True)
        
        for d in dados:
            pasta = d['pasta']
            if pasta:
                if pasta not in nos_pasta:
                    nos_pasta[pasta] = tree.insert("", "end", text=pasta, open=True)
                pai = nos_pasta[pasta]
            else:
                pai = raiz_geral
            
            tree.insert(pai, "end", text=d['titulo'], values=("entry", d['id']))

def acao_adicionar():
    tit = WIDGETS["title"].get()
    pwd = WIDGETS["password"].get()
    
    if not tit or not pwd:
        messagebox.showwarning("Erro", "Título e password são obrigatórios.")
        return

    # Verificar duplicados pelo titulo (opcional, mas bom pra evitar confusão)
    todos = storage.ler_todas_passwords()
    if any(d['titulo'] == tit for d in todos):
        messagebox.showerror("Erro", "Já existe uma entrada com esse título.")
        return

    storage.adicionar_password(WIDGETS["folder"].get(), tit, WIDGETS["url"].get(), WIDGETS["user"].get(), pwd)
    atualizar_lista()
    limpar_formulario()
    messagebox.showinfo("Sucesso", "Adicionado!")

def acao_atualizar():
    if not APP_ESTADO["id_selecionado"]:
        messagebox.showwarning("Aviso", "Selecione algo para editar.")
        return
        
    # Truque simples: Apaga o antigo e cria o novo
    storage.apagar_password(APP_ESTADO["id_selecionado"])
    storage.adicionar_password(WIDGETS["folder"].get(), WIDGETS["title"].get(), WIDGETS["url"].get(), WIDGETS["user"].get(), WIDGETS["password"].get())
    
    atualizar_lista()
    limpar_formulario()
    messagebox.showinfo("Sucesso", "Atualizado!")

def acao_apagar():
    if APP_ESTADO["id_selecionado"]:
        if messagebox.askyesno("Apagar", "Tem a certeza?"):
            storage.apagar_password(APP_ESTADO["id_selecionado"])
            atualizar_lista()
            limpar_formulario()

def ao_selecionar_tree(event):
    sel = WIDGETS["tree"].selection()
    if not sel: return
    
    valores = WIDGETS["tree"].item(sel[0], "values")
    # Se tiver valores ("entry", id), é um item. Se não, é pasta.
    if valores and valores[0] == "entry":
        id_db = int(valores[1])
        # Busca os dados completos
        todos = storage.ler_todas_passwords()
        for d in todos:
            if d['id'] == id_db:
                preencher_formulario(d)
                break
    else:
        limpar_formulario()

# ================= 4. Construção da Janela Principal =================

def abrir_janela_principal(algo_nome):
    root = tk.Tk()
    APP_ESTADO["root"] = root
    APP_ESTADO["ultimo_toque"] = time.time()
    
    root.title(f"SRC Password Manager - {algo_nome.upper()}")
    root.geometry("1000x580")
    
    # Configurar Estilos das Barras
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Red.Horizontal.TProgressbar", foreground='red', background='red')
    style.configure("Yellow.Horizontal.TProgressbar", foreground='#FFAA00', background='#FFAA00')
    style.configure("Green.Horizontal.TProgressbar", foreground='green', background='green')
    
    # Detetar inatividade em qualquer tecla ou clique
    root.bind_all("<Any-KeyPress>", resetar_timer)
    root.bind_all("<Any-Button>", resetar_timer)
    
    # Layout Esquerdo (Lista)
    frame_left = tk.Frame(root)
    frame_left.pack(side="left", fill="both", expand=True, padx=15, pady=15)
    
    # Pesquisa
    frame_search = tk.Frame(frame_left)
    frame_search.pack(fill="x", pady=(0, 10))
    tk.Label(frame_search, text="🔍").pack(side="left")
    entry_search = tk.Entry(frame_search)
    entry_search.pack(side="left", fill="x", expand=True)
    entry_search.bind("<KeyRelease>", lambda e: atualizar_lista(entry_search.get()))

    # Treeview
    tree = ttk.Treeview(frame_left, columns=("type", "id"), show="tree", selectmode="browse")
    tree["displaycolumns"] = () # Esconde as colunas de dados, mostra so a arvore
    tree.pack(side="top", fill="both", expand=True)
    tree.bind("<<TreeviewSelect>>", ao_selecionar_tree)
    WIDGETS["tree"] = tree
    
    # Botão Auditoria
    tk.Button(frame_left, text="♻ Verificar passwords Repetidas", command=abrir_auditoria, bg="#ffebcd").pack(fill="x", pady=10)

    # Layout Direito (Formulário)
    frame_right = tk.Frame(root)
    frame_right.pack(side="right", fill="both", padx=20, pady=15)

    def criar_linha(rotulo, row, combobox=False):
        tk.Label(frame_right, text=rotulo).grid(row=row, column=0, sticky="e", padx=5, pady=5)
        if combobox:
            w = ttk.Combobox(frame_right, width=43)
        else:
            w = tk.Entry(frame_right, width=45)
        w.grid(row=row, column=1, padx=5, pady=5)
        return w

    WIDGETS["folder"] = criar_linha("Pasta / Categoria:", 0, combobox=True)
    WIDGETS["title"] = criar_linha("Título:", 1)
    WIDGETS["url"] = criar_linha("URL:", 2)
    WIDGETS["user"] = criar_linha("Utilizador:", 3)

    # Password com botões extra
    tk.Label(frame_right, text="Password:").grid(row=4, column=0, sticky="e", padx=5)
    entry_pw = tk.Entry(frame_right, width=45, show="*")
    entry_pw.grid(row=4, column=1, padx=5, pady=5)
    entry_pw.bind("<KeyRelease>", atualizar_barra_entropia_da_password)
    WIDGETS["password"] = entry_pw

    # Barra de Ferramentas da Password
    frame_tools = tk.Frame(frame_right)
    frame_tools.grid(row=4, column=2, sticky="w", padx=5)
    tk.Button(frame_tools, text="👁", width=3, command=toggle_ver_password).pack(side="left", padx=1)
    tk.Button(frame_tools, text="⚙", width=3, command=abrir_gerador_passwords).pack(side="left", padx=1)
    tk.Button(frame_tools, text="⌨", width=3, command=lambda: abrir_teclado_virtual(entry_pw)).pack(side="left", padx=1)
    tk.Button(frame_tools, text="📋", width=3, command=copiar_password).pack(side="left", padx=1)

    # Barra de Progresso (Entropia)
    lbl_forca = tk.Label(frame_right, text="Força: N/A", font=("Arial", 8))
    lbl_forca.grid(row=5, column=1, sticky="w", padx=5)
    progress = ttk.Progressbar(frame_right, orient="horizontal", length=275, mode="determinate")
    progress.grid(row=6, column=1, sticky="w", padx=5)
    WIDGETS["lbl_forca"] = lbl_forca
    WIDGETS["progress"] = progress

    # Botões de Ação
    frame_btns = tk.Frame(frame_right)
    frame_btns.grid(row=8, column=0, columnspan=3, pady=30)
    
    tk.Button(frame_btns, text="Adicionar", command=acao_adicionar, bg="#ddffdd", width=12).pack(side="left", padx=5)
    tk.Button(frame_btns, text="Atualizar", command=acao_atualizar, bg="#fffddd", width=12).pack(side="left", padx=5)
    tk.Button(frame_btns, text="Limpar", command=limpar_formulario, width=8).pack(side="left", padx=5)
    tk.Button(frame_btns, text="Eliminar", command=acao_apagar, bg="#ffdddd", width=10).pack(side="left", padx=15)

    tk.Button(root, text="Sair", command=root.destroy, bg="#e0e0e0").place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

    atualizar_lista()
    verificar_inatividade() # Começa o timer
    root.mainloop()

# ================= 5. Menus de Entrada =================

def menu_inicial():
    root = tk.Tk()
    root.title("Gestor Seguro")
    root.geometry("350x200")
    
    escolha = {"tipo": None}

    def ir_abrir(): escolha["tipo"] = "abrir"; root.destroy()
    def ir_criar(): escolha["tipo"] = "criar"; root.destroy()

    tk.Label(root, text="Gestor de Passwords", font=("Arial", 14, "bold")).pack(pady=20)
    tk.Button(root, text="Abrir cofre existente", command=ir_abrir, width=20).pack(pady=5)
    tk.Button(root, text="Criar novo cofre", command=ir_criar, width=20).pack(pady=5)
    root.mainloop()
    
    if not escolha["tipo"]: return # Fechou a janela

    if escolha["tipo"] == "abrir":
        db_path = filedialog.askopenfilename(title="Abrir", filetypes=[("Cofre", "*.db")])
        if not db_path: return menu_inicial()
        
        storage.configurar_storage(db_path)
        
        # Loop login
        while True:
            # Janela invisível para o dialogo
            tmp = tk.Tk(); tmp.withdraw()
            pwd = simpledialog.askstring("Login", "Password Mestra:", show="*")
            tmp.destroy()
            
            if not pwd: return menu_inicial() # Cancelou
            
            if storage.tentar_abrir_cofre(pwd):
                abrir_janela_principal(storage.ALGORITMO_ATUAL)
                break
            else:
                messagebox.showerror("Erro", "Password Errada!")

    elif escolha["tipo"] == "criar":
        db_path = filedialog.asksaveasfilename(title="Novo", defaultextension=".db", filetypes=[("Cofre", "*.db")])
        if not db_path: return menu_inicial()
        
        # Diálogo customizado para password + algoritmo
        cfg = {"pw": None, "algo": "aes-gcm"}
        
        d = tk.Toplevel()
        d.title("Configurar")
        d.geometry("300x250")
        tk.Label(d, text="Nova Password Mestra:").pack(pady=5)
        e = tk.Entry(d, show="*"); e.pack()
        tk.Label(d, text="Algoritmo:").pack(pady=5)
        c = ttk.Combobox(d, values=["aes-gcm", "chacha20", "fernet"], state="readonly")
        c.current(0); c.pack()
        
        def ok():
            if not e.get(): return
            cfg["pw"] = e.get()
            cfg["algo"] = c.get()
            d.destroy()
            
        tk.Button(d, text="Criar", command=ok, bg="#ddffdd").pack(pady=20)
        # Espera fechar
        # Precisamos de um root temporario para o wait_window funcionar se o menu ja fechou
        dummy = tk.Tk(); dummy.withdraw()
        d.transient(dummy)
        d.wait_window()
        dummy.destroy()
        
        if cfg["pw"]:
            storage.configurar_storage(db_path)
            storage.criar_novo_cofre(cfg["pw"], cfg["algo"])
            abrir_janela_principal(cfg["algo"])
        else:
            menu_inicial()

if __name__ == "__main__":
    menu_inicial()