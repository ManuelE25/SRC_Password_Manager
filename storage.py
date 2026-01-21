# storage.py
import sqlite3
import os
import crypto_utils as crypto

# Variáveis Globais de Estado
CAMINHO_DB = None
CHAVE_ATUAL = None
ALGORITMO_ATUAL = "aes-gcm" # Padrão

def conectar():
    return sqlite3.connect(CAMINHO_DB)

def configurar_storage(caminho):
    global CAMINHO_DB
    CAMINHO_DB = caminho
    
    conn = conectar()
    # Tabela de configurações
    conn.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value BLOB
        );
    """)
    # Tabela de passwords
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pasta TEXT,
            titulo TEXT,
            url TEXT,
            usuario TEXT,
            password TEXT
        );
    """)
    conn.commit()
    conn.close()

def criar_novo_cofre(password_mestra, algoritmo_escolhido="aes-gcm"):
    global CHAVE_ATUAL, ALGORITMO_ATUAL
    
    ALGORITMO_ATUAL = algoritmo_escolhido
    salt = os.urandom(16)
    CHAVE_ATUAL = crypto.criar_chave_secreta(password_mestra, salt)
    
    # Validação para testar se a password está certa no futuro
    teste_validacao = crypto.cifrar(ALGORITMO_ATUAL, CHAVE_ATUAL, "CHECK_OK")
    
    conn = conectar()
    # Guardamos o Sal, o Algoritmo e a Validação
    conn.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", ("salt", salt))
    conn.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", ("algo", algoritmo_escolhido.encode()))
    conn.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", ("val", teste_validacao.encode()))
    conn.commit()
    conn.close()

def tentar_abrir_cofre(password_mestra):
    global CHAVE_ATUAL, ALGORITMO_ATUAL
    
    conn = conectar()
    cursor = conn.cursor()
    
    row_salt = cursor.execute("SELECT value FROM metadata WHERE key='salt'").fetchone()
    row_algo = cursor.execute("SELECT value FROM metadata WHERE key='algo'").fetchone()
    row_val = cursor.execute("SELECT value FROM metadata WHERE key='val'").fetchone()
    conn.close()
    
    if not row_salt or not row_val:
        return False
        
    salt = row_salt[0]
    # Se existir algoritmo salvo, usa-o, senão usa o padrão aes-gcm
    ALGORITMO_ATUAL = row_algo[0].decode() if row_algo else "aes-gcm"
    
    chave_tentativa = crypto.criar_chave_secreta(password_mestra, salt)
    
    # Tenta decifrar a validação
    resultado = crypto.decifrar(ALGORITMO_ATUAL, chave_tentativa, row_val[0].decode())
    
    if resultado == "CHECK_OK":
        CHAVE_ATUAL = chave_tentativa
        return True
    return False

def adicionar_password(pasta, titulo, url, usuario, password):
    if not CHAVE_ATUAL: return False
    
    # Cifra tudo com o algoritmo atual
    p = crypto.cifrar(ALGORITMO_ATUAL, CHAVE_ATUAL, pasta)
    t = crypto.cifrar(ALGORITMO_ATUAL, CHAVE_ATUAL, titulo)
    u = crypto.cifrar(ALGORITMO_ATUAL, CHAVE_ATUAL, url)
    user = crypto.cifrar(ALGORITMO_ATUAL, CHAVE_ATUAL, usuario)
    s = crypto.cifrar(ALGORITMO_ATUAL, CHAVE_ATUAL, password)
    
    conn = conectar()
    conn.execute(
        "INSERT INTO entries (pasta, titulo, url, usuario, password) VALUES (?, ?, ?, ?, ?)",
        (p, t, u, user, s)
    )
    conn.commit()
    conn.close()
    return True

def ler_todas_passwords():
    if not CHAVE_ATUAL: return []
    
    conn = conectar()
    linhas = conn.execute("SELECT id, pasta, titulo, url, usuario, password FROM entries").fetchall()
    conn.close()
    
    lista = []
    for pid, p, t, u, usr, s in linhas:
        try:
            item = {
                "id": pid,
                "pasta": crypto.decifrar(ALGORITMO_ATUAL, CHAVE_ATUAL, p),
                "titulo": crypto.decifrar(ALGORITMO_ATUAL, CHAVE_ATUAL, t),
                "url": crypto.decifrar(ALGORITMO_ATUAL, CHAVE_ATUAL, u),
                "utilizador": crypto.decifrar(ALGORITMO_ATUAL, CHAVE_ATUAL, usr),
                "password": crypto.decifrar(ALGORITMO_ATUAL, CHAVE_ATUAL, s)
            }
            lista.append(item)
        except:
            continue
            
    lista.sort(key=lambda x: (x['pasta'], x['titulo']))
    return lista

def apagar_password(id_reg):
    conn = conectar()
    conn.execute("DELETE FROM entries WHERE id = ?", (id_reg,))
    conn.commit()
    conn.close()