import sqlite3
import os

# Chemin vers la base de données
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "app.db")

try:
    # Établir la connexion
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Vérifier simplement si la connexion est fonctionnelle
    cursor.execute("SELECT sqlite_version()")
    version = cursor.fetchone()[0]
    
    print(f"✅ Connexion réussie à SQLite version {version}")
    
    # Vérifier les tables existantes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("\nTables disponibles dans la base de données:")
    for table in tables:
        print(f"- {table[0]}")
    
    # Vérifier si la table 'users' existe
    if any(table[0] == 'users' for table in tables):
        # Compter les lignes dans la table 'users'
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        print(f"\nLa table 'users' contient {count} ligne(s)")
    else:
        print("\n⚠️ La table 'users' n'existe pas dans la base de données")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Erreur de connexion : {e}")
    print(f"Chemin utilisé : {db_path}")
    
    # Vérification supplémentaire
    if not os.path.exists(os.path.dirname(db_path)):
        print(f"⚠️ Le dossier '{os.path.dirname(db_path)}' est introuvable")
    elif not os.path.exists(db_path):
        print(f"⚠️ Le fichier de base de données est introuvable")