import sqlite3
import os

# Créer le dossier s'il n'existe pas
os.makedirs("db", exist_ok=True)

# Connexion à SQLite
conn = sqlite3.connect("db/app.db")
cursor = conn.cursor()

# Activer les clés étrangères
cursor.execute("PRAGMA foreign_keys = ON;")

# Script SQL pour créer les tables
cursor.executescript("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS db_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    host TEXT NOT NULL,
    port INTEGER NOT NULL,
    db TEXT NOT NULL,
    user TEXT,
    password TEXT
);

CREATE TABLE IF NOT EXISTS queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sql_text TEXT NOT NULL,
    parameters TEXT,
    roles TEXT,
    db_id INTEGER,
    FOREIGN KEY (db_id) REFERENCES db_connections(id)
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    query_id INTEGER,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT,
    message TEXT
);
""")

conn.commit()
conn.close()

print("✅ app.db créé correctement dans le dossier /db")
