import sqlite3
import os

# Chemin correct si ce script est dans le dossier /db
DB_PATH = os.path.join(os.path.dirname(__file__), 'app.db')

# Connexion
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Ajouter la colonne email
try:
    cur.execute("ALTER TABLE users ADD COLUMN email TEXT")
    print("✅ Colonne 'email' ajoutée.")
except sqlite3.OperationalError as e:
    print(f"ℹ️ {e}")  # Probablement déjà ajoutée

conn.commit()
conn.close()
