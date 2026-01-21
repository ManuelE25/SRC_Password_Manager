# crypto_utils.py
import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend

# Configurações
ITERACOES = 600_000

def criar_chave_secreta(password, salt):
    # Cria uma chave de 32 bytes a partir da senha
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERACOES,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

def cifrar(algoritmo, chave, texto):
    if not texto: return ""
    dados = texto.encode()
    
    # 1. AES-GCM (Padrão e Rápido)
    if algoritmo == "aes-gcm":
        aes = AESGCM(chave)
        nonce = os.urandom(12)
        cifrado = aes.encrypt(nonce, dados, None)
        return base64.b64encode(nonce + cifrado).decode()
    
    # 2. ChaCha20 (Moderno e Seguro)
    elif algoritmo == "chacha20":
        chacha = ChaCha20Poly1305(chave)
        nonce = os.urandom(12)
        cifrado = chacha.encrypt(nonce, dados, None)
        return base64.b64encode(nonce + cifrado).decode()
        
    # 3. Fernet (Simples e popular em Python)
    elif algoritmo == "fernet":
        # Fernet precisa da chave em formato URL-Safe Base64
        chave_b64 = base64.urlsafe_b64encode(chave)
        f = Fernet(chave_b64)
        return f.encrypt(dados).decode()
        
    else:
        raise ValueError("Algoritmo desconhecido: " + algoritmo)

def decifrar(algoritmo, chave, texto_codificado):
    if not texto_codificado: return ""
    
    try:
        dados_brutos = base64.b64decode(texto_codificado)
        
        if algoritmo == "aes-gcm":
            nonce = dados_brutos[:12]
            cifrado = dados_brutos[12:]
            return AESGCM(chave).decrypt(nonce, cifrado, None).decode()
            
        elif algoritmo == "chacha20":
            nonce = dados_brutos[:12]
            cifrado = dados_brutos[12:]
            return ChaCha20Poly1305(chave).decrypt(nonce, cifrado, None).decode()
            
        elif algoritmo == "fernet":
            # Para Fernet usamos o texto original, não o decode inicial
            chave_b64 = base64.urlsafe_b64encode(chave)
            f = Fernet(chave_b64)
            # O Fernet faz o próprio decode base64 internamente
            return f.decrypt(texto_codificado.encode()).decode()
            
    except Exception:
        return None # Falha na senha ou dados corrompidos
        
    return None