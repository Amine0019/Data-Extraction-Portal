import sqlite3
import os
import re
import bcrypt

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'app.db')

ROLES = {"Admin", "Analyste", "Utilisateur"}
ACTIVE_STATES = {"is_active": 1, "not_active": 0}

# --- VALIDATIONS ---
def validate_username(username):
    if not isinstance(username, str):
        return False, "Le nom d'utilisateur doit être une chaîne de caractères."
    if not (3 <= len(username) <= 50):
        return False, "Le nom d'utilisateur doit contenir entre 3 et 50 caractères."
    if not re.match(r'^[A-Za-z0-9_]+$', username):
        return False, "Le nom d'utilisateur doit être alphanumérique (lettres, chiffres, underscore)."
    return True, ""

def validate_password(password):
    if not isinstance(password, str):
        return False, "Le mot de passe doit être une chaîne de caractères."
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    return True, ""

def validate_role(role):
    if role not in ROLES:
        return False, f"Le rôle doit être parmi {ROLES}."
    return True, ""

def validate_is_active(is_active):
    if is_active not in (0, 1):
        return False, "Le champ 'actif ?' doit être 1 (is_active) ou 0 (not_active)."
    return True, ""

# --- DB CONNECTION ---
def get_db_conn():
    return sqlite3.connect(DB_PATH)

# --- CRUD ---
def get_all_users():
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, is_active FROM users ORDER BY id ASC")
    users = cursor.fetchall()
    conn.close()
    return users

def get_user_by_username(username):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_user(username, password, role, is_active):
    # Validations
    valid, msg = validate_username(username)
    if not valid:
        return False, msg
    valid, msg = validate_password(password)
    if not valid:
        return False, msg
    valid, msg = validate_role(role)
    if not valid:
        return False, msg
    valid, msg = validate_is_active(is_active)
    if not valid:
        return False, msg
    # Unicité username
    if get_user_by_username(username):
        return False, "Ce nom d'utilisateur existe déjà."
    # Hashage du mot de passe
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, role, is_active) VALUES (?, ?, ?, ?)",
            (username, hashed, role, is_active)
        )
        conn.commit()
        conn.close()
        return True, "Utilisateur ajouté avec succès."
    except Exception as e:
        return False, f"Erreur lors de l'ajout : {e}"

def update_user(user_id, fields_to_update):
    allowed_fields = {"username", "password", "role", "is_active"}
    set_clauses = []
    values = []
    # Validations
    if "username" in fields_to_update:
        valid, msg = validate_username(fields_to_update["username"])
        if not valid:
            return False, msg
        # Unicité username (hors soi-même)
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (fields_to_update["username"],))
        user = cursor.fetchone()
        conn.close()
        if user and user[0] != user_id:
            return False, "Ce nom d'utilisateur existe déjà."
        set_clauses.append("username = ?")
        values.append(fields_to_update["username"])
    if "password" in fields_to_update:
        valid, msg = validate_password(fields_to_update["password"])
        if not valid:
            return False, msg
        hashed = bcrypt.hashpw(fields_to_update["password"].encode(), bcrypt.gensalt())
        set_clauses.append("password = ?")
        values.append(hashed)
    if "role" in fields_to_update:
        valid, msg = validate_role(fields_to_update["role"])
        if not valid:
            return False, msg
        set_clauses.append("role = ?")
        values.append(fields_to_update["role"])
    if "is_active" in fields_to_update:
        valid, msg = validate_is_active(fields_to_update["is_active"])
        if not valid:
            return False, msg
        set_clauses.append("is_active = ?")
        values.append(fields_to_update["is_active"])
    if not set_clauses:
        return False, "Aucune donnée à mettre à jour."
    values.append(user_id)
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?", values)
        conn.commit()
        conn.close()
        return True, "Utilisateur modifié avec succès."
    except Exception as e:
        return False, f"Erreur lors de la modification : {e}"

def delete_user(user_id, current_admin_id):
    if user_id == current_admin_id:
        return False, "Vous ne pouvez pas supprimer votre propre compte."
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True, "Utilisateur supprimé avec succès."
    except Exception as e:
        return False, f"Erreur lors de la suppression : {e}" 