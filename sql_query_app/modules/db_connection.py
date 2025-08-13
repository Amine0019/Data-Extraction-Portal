import pyodbc
import sqlite3
import os
import re
import streamlit as st
from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv
from pathlib import Path

# --- CHARGEMENT DES VARIABLES D'ENVIRONNEMENT ---
load_dotenv()  # Charger les variables du fichier .env

# --- CONFIGURATION ---
# Chemin absolu vers le dossier db (sql_query_app/db)
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)  # Crée le dossier si nécessaire
DB_PATH = str(DB_DIR / "app.db")

FERNET_KEY = os.getenv("FERNET_KEY")  # Clé dans .env

if not FERNET_KEY:
    raise ValueError("La clé Fernet n'est pas définie dans les variables d'environnement.")

fernet = Fernet(FERNET_KEY.encode())

# --- VALIDATIONS ---
def validate_connection_name(name):
    if not (3 <= len(name) <= 50):
        return False, "Le nom de la connexion doit contenir entre 3 et 50 caractères."
    if not re.match(r'^[A-Za-z0-9_\- ]+$', name):
        return False, "Le nom doit contenir uniquement des lettres, chiffres, espaces, tirets et underscores."
    return True, ""

def validate_host(host):
    if not host or len(host) < 3:
        return False, "L'hôte doit contenir au moins 3 caractères."
    return True, ""

def validate_port(port):
    try:
        port_int = int(port)
        if not (1 <= port_int <= 65535):
            return False, "Le port doit être entre 1 et 65535."
        return True, ""
    except ValueError:
        return False, "Le port doit être un nombre entier."

def validate_db_service(service):
    if not service or len(service) < 1:
        return False, "Le nom du service/base est requis."
    return True, ""

def validate_user(user):
    if not user or len(user) < 1:
        return False, "Le nom d'utilisateur est requis."
    return True, ""

# --- CHIFFREMENT ---
def encrypt_password(password: str) -> str:
    return fernet.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    return fernet.decrypt(encrypted_password.encode()).decode()

# --- CRUD DB_CONNECTIONS ---
def get_connection_info(conn_id: int):
    """Récupère les infos de connexion avec mot de passe déchiffré et port en int"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, type, host, port, db_service, user, password 
        FROM db_connections WHERE id = ?
    """, (conn_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        try:
            password = decrypt_password(row[7])
        except InvalidToken:
            password = ""
            st.error("❌ Erreur de déchiffrement - Clé Fernet invalide ou données corrompues")
        
        # Conversion du port en int avec fallback sur 1433
        try:
            port_value = int(row[4]) if row[4] is not None else 1433
        except (ValueError, TypeError):
            port_value = 1433
        
        return {
            "id": row[0],
            "name": row[1],
            "type": row[2],
            "host": row[3],
            "port": port_value,
            "db_service": row[5],
            "user": row[6],
            "password": password
        }
    return None


def add_connection(data: dict):
    """Ajoute une nouvelle connexion avec validation et chiffrement"""
    # Validations
    validations = [
        validate_connection_name(data["name"]),
        validate_host(data["host"]),
        validate_port(data["port"]),
        validate_db_service(data["db_service"]),
        validate_user(data["user"])
    ]
    
    for valid, msg in validations:
        if not valid:
            return False, msg
    
    # Vérifier l'unicité du nom
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM db_connections WHERE name = ?", (data["name"],))
    if cursor.fetchone():
        conn.close()
        return False, "Ce nom de connexion existe déjà."
    
    try:
        # Chiffrer le mot de passe
        encrypted_pwd = encrypt_password(data["password"])
        
        cursor.execute("""
            INSERT INTO db_connections (name, type, host, port, db_service, user, password)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data["name"],
            data["type"],
            data["host"],
            int(data["port"]),
            data["db_service"],
            data["user"],
            encrypted_pwd
        ))
        conn.commit()
        return True, "Connexion ajoutée avec succès."
    except Exception as e:
        return False, f"Erreur lors de l'ajout: {str(e)}"
    finally:
        conn.close()

def update_connection(conn_id: int, data: dict):
    """Met à jour une connexion existante"""
    # Validations
    validations = [
        validate_connection_name(data["name"]),
        validate_host(data["host"]),
        validate_port(data["port"]),
        validate_db_service(data["db_service"]),
        validate_user(data["user"])
    ]
    
    for valid, msg in validations:
        if not valid:
            return False, msg
    
    # Vérifier l'unicité du nom (exclure l'actuel)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM db_connections WHERE name = ? AND id != ?", 
                  (data["name"], conn_id))
    if cursor.fetchone():
        conn.close()
        return False, "Ce nom de connexion existe déjà."
    
    try:
        # Chiffrer le mot de passe
        encrypted_pwd = encrypt_password(data["password"])
        
        cursor.execute("""
            UPDATE db_connections
            SET name=?, type=?, host=?, port=?, db_service=?, user=?, password=?
            WHERE id=?
        """, (
            data["name"],
            data["type"],
            data["host"],
            int(data["port"]),
            data["db_service"],
            data["user"],
            encrypted_pwd,
            conn_id
        ))
        conn.commit()
        return True, "Connexion mise à jour avec succès."
    except Exception as e:
        return False, f"Erreur lors de la mise à jour: {str(e)}"
    finally:
        conn.close()

def delete_connection(conn_id: int):
    """Supprime une connexion par son ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM db_connections WHERE id=?", (conn_id,))
        conn.commit()
        return True, "Connexion supprimée avec succès."
    except Exception as e:
        return False, f"Erreur lors de la suppression: {str(e)}"
    finally:
        conn.close()

def get_all_connections():
    """Récupère toutes les connexions (sans les mots de passe) et convertit port en int"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, type, host, port, db_service, user
        FROM db_connections
        ORDER BY name
    """)
    rows = cursor.fetchall()
    conn.close()

    # Conversion du port en int pour chaque ligne
    corrected_rows = []
    for row in rows:
        try:
            port_value = int(row[4]) if row[4] is not None else 1433
        except (ValueError, TypeError):
            port_value = 1433
        
        corrected_rows.append((
            row[0],  # id
            row[1],  # name
            row[2],  # type
            row[3],  # host
            port_value,
            row[5],  # db_service
            row[6]   # user
        ))

    return corrected_rows

def test_connection(conn_id: int):
    """Teste une connexion par son ID"""
    conn_info = get_connection_info(conn_id)
    if not conn_info:
        return False, "Connexion non trouvée"
    
    if conn_info["type"].lower() != "sqlserver":
        return False, "Seul SQL Server est supporté"
    
    return test_sql_server_connection(conn_info)

def test_sql_server_connection(conn_info):
    """Teste la connexion à SQL Server avec messages d'erreurs plus clairs."""
    try:
        if conn_info["user"] == "" and conn_info["password"] == "":
            # Authentification Windows
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={conn_info['host']},{conn_info['port']};"
                f"DATABASE={conn_info['db_service']};"
                f"Trusted_Connection=yes;"
            )
        else:
            # Authentification SQL Server
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={conn_info['host']},{conn_info['port']};"
                f"DATABASE={conn_info['db_service']};"
                f"UID={conn_info['user']};"
                f"PWD={conn_info['password']};"
            )

        conn = pyodbc.connect(conn_str, timeout=5)  # timeout pour éviter attente infinie
        conn.close()
        return True, "✅ Connexion réussie !"

    except pyodbc.InterfaceError as e:
        return False, "❌ Impossible d'atteindre le serveur. Vérifiez l'adresse et le port."
    except pyodbc.OperationalError as e:
        msg = str(e)
        if "Login failed" in msg or "Echec de la connexion" in msg:
            return False, "❌ Nom d'utilisateur ou mot de passe incorrect."
        elif "timeout" in msg.lower():
            return False, "⏳ Temps d'attente dépassé. Vérifiez si le serveur est en ligne."
        else:
            return False, f"❌ Erreur opérationnelle : {msg}"
    except Exception as e:
        return False, f"❌ Erreur inconnue : {str(e)}"
        
class DatabaseConnection:
    def __init__(self, conn_info):
        try:
            if conn_info["type"].lower() == "sqlserver":
                if conn_info["user"] == "" and conn_info["password"] == "":
                    # Authentification Windows
                    conn_str = (
                        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                        f"SERVER={conn_info['host']},{conn_info['port']};"
                        f"DATABASE={conn_info['db_service']};"
                        f"Trusted_Connection=yes;"
                    )
                else:
                    # Authentification SQL Server
                    conn_str = (
                        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                        f"SERVER={conn_info['host']},{conn_info['port']};"
                        f"DATABASE={conn_info['db_service']};"
                        f"UID={conn_info['user']};"
                        f"PWD={conn_info['password']};"
                    )
            else:
                raise ValueError("Seul SQL Server est supporté")

            self._connection = pyodbc.connect(conn_str)
        except Exception as e:
            self._connection = None
            print("❌ Erreur de connexion :", e)

    def get_connection(self):
        return self._connection

    def close(self):
        if self._connection:
            self._connection.close()

# --- INITIALISATION DE LA BASE ---
def init_db():
    """Initialise la base de données si elle n'existe pas"""
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS db_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                db_service TEXT NOT NULL,
                user TEXT NOT NULL,
                password TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        print(f"Base de données initialisée: {DB_PATH}")

# --- FONCTION UTILITAIRE POUR LES TESTS ---
def cleanup_test_connections(base_name: str):
    """Nettoie les connexions de test existantes"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM db_connections WHERE name LIKE ? || '%'", 
            (base_name,)
        )
        deleted_count = cursor.rowcount
        conn.commit()
    print(f"{deleted_count} anciennes connexions nettoyées")

# --- TEST ---
if __name__ == "__main__":
    # Initialiser la base de données
    init_db()
    
    print(f"Chemin DB: {DB_PATH}")
    print(f"DB existe: {os.path.exists(DB_PATH)}")
    
    # Nettoyer les anciennes connexions de test
    BASE_TEST_NAME = "SQL Server Test"
    cleanup_test_connections(BASE_TEST_NAME)
    
    # Exemple d'ajout de connexion
    new_conn = {
        "name": BASE_TEST_NAME,
        "type": "sqlserver",
        "host": "localhost",
        "port": 1433,
        "db_service": "master",
        "user": "sa",
        "password": "votre_mot_de_passe_sa"  # REMPLACEZ PAR VOTRE VRAI MOT DE PASSE
    }
    
    # Ajouter la connexion
    success, message = add_connection(new_conn)
    print(f"Ajout: {success} - {message}")
    
    # Tester la connexion
    if success:
        # Récupérer l'ID de la connexion par son nom
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM db_connections WHERE name = ?", (BASE_TEST_NAME,))
            result = cursor.fetchone()
            if result:
                conn_id = result[0]
            else:
                print("❌ La connexion n'a pas été trouvée après l'ajout")
                exit(1)
        
        # Tester la connexion
        success, message = test_connection(conn_id)
        print(f"Test: {success} - {message}")
        
        # Utiliser la connexion
        try:
            conn_info = get_connection_info(conn_id)
            if conn_info:
                print("\nConfiguration de connexion utilisée:")
                print(f"Type: {conn_info['type']}")
                print(f"Host: {conn_info['host']}")
                print(f"Port: {conn_info['port']}")
                print(f"DB: {conn_info['db_service']}")
                print(f"User: {conn_info['user']}")
                
                db = DatabaseConnection(conn_info)
                conn_db = db.get_connection()
                if conn_db:
                    print("\n✅ Connexion établie avec succès!")
                    
                    # Tester la requête
                    cursor = conn_db.cursor()
                    cursor.execute("SELECT TOP 1 name FROM sys.databases")
                    row = cursor.fetchone()
                    
                    if row:
                        print(f"Première base: {row[0]}")
                    else:
                        print("Aucun résultat retourné")
                    
                    # Nettoyage
                    cursor.close()
                    db.close()
                    print("Connexion fermée proprement")
                else:
                    print("❌ Échec de la connexion via DatabaseConnection")
            else:
                print("❌ Informations de connexion non trouvées")
        except pyodbc.Error as e:
            print(f"\n❌ Erreur pyodbc: {str(e)}")
            print("Code d'état SQL:", e.args[0] if e.args else "Inconnu")
        except Exception as e:
            print(f"\n❌ Erreur générale: {str(e)}")
    else:
        print("❌ Échec de l'ajout de la connexion, impossible de tester")