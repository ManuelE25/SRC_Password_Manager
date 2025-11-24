import sqlite3
import tkinter as tk
from tkinter import messagebox

def init_db():
    conn = sqlite3.connect('password_manager.db')
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

def add():
    username = entryName.get()
    password = entryPassword.get()
    if username and password:
        conn = sqlite3.connect('password_manager.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO passwords (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        messagebox.showinfo("Sucesso", "Password adicionada!")
    else:
        messagebox.showerror("Erro", "Preenche ambos os campos.")

def get():
    username = entryName.get()
    conn = sqlite3.connect('password_manager.db')
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM passwords WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    if result:
        messagebox.showinfo("Resultado", f"Password para {username}: {result[0]}")
    else:
        messagebox.showinfo("Resultado", "Utilizador não encontrado.")

def getlist():
    conn = sqlite3.connect('password_manager.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM passwords")
    rows = cursor.fetchall()
    conn.close()
    if rows:
        mess = "Passwords guardadas:\n"
        for row in rows:
            mess += f"{row[0]}: {row[1]}\n"
        messagebox.showinfo("Lista de passwords", mess)
    else:
        messagebox.showinfo("Lista de passwords", "Nenhuma password encontrada.")

def delete():
    username = entryName.get()
    conn = sqlite3.connect('password_manager.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM passwords WHERE username = ?", (username,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    if affected:
        messagebox.showinfo("Sucesso", f"Utilizador {username} eliminado!")
    else:
        messagebox.showinfo("INFO", f"Utilizador {username} não encontrado.")

if __name__ == "__main__":
    init_db()

    app = tk.Tk()
    app.geometry("450x210")
    app.title("Gestor de Passwords")

    labelName = tk.Label(app, text="Utilizador/Site:")
    labelName.grid(row=0, column=0, padx=15, pady=15)
    entryName = tk.Entry(app)
    entryName.grid(row=0, column=1, padx=15, pady=15)

    labelPassword = tk.Label(app, text="Password:")
    labelPassword.grid(row=1, column=0, padx=10, pady=5)
    entryPassword = tk.Entry(app)
    entryPassword.grid(row=1, column=1, padx=10, pady=5)

    buttonAdd = tk.Button(app, text="Adicionar", command=add)
    buttonAdd.grid(row=2, column=0, padx=15, pady=8, sticky="we")

    buttonGet = tk.Button(app, text="Pesquisar", command=get)
    buttonGet.grid(row=2, column=1, padx=15, pady=8, sticky="we")

    buttonList = tk.Button(app, text="Listar", command=getlist)
    buttonList.grid(row=3, column=0, padx=15, pady=8, sticky="we")

    buttonDelete = tk.Button(app, text="Eliminar", command=delete)
    buttonDelete.grid(row=3, column=1, padx=15, pady=8, sticky="we")

    app.mainloop()
