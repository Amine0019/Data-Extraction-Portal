import sqlite3
import re
import bcrypt
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'app.db')

ROLES = {"Admin", "Analyste", "Utilisateur"}
ACTIVE_STATES = {"is_active": 1, "not_active": 0}

# --- VALIDATIONS ---
def validate_username(username):
    if not (3 <= len(username) <= 50):
        return False, "Le nom d'utilisateur doit contenir entre 3 et 50 caractères."
    if not re.match(r'^[A-Za-z0-9_]+$', username):  # Autoriser aussi les chiffres
        return False, "Le nom d'utilisateur doit contenir uniquement des lettres, chiffres et underscores."
    return True, ""

def validate_password(password):
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    return True, ""

def validate_email(email):
    if not email or not isinstance(email, str):
        return False, "Adresse email invalide."
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        return False, "Adresse email invalide."
    return True, ""

def validate_role(role):
    if role not in ROLES:
        return False, f"Le rôle doit être parmi {', '.join(ROLES)}."
    return True, ""

def validate_is_active(is_active):
    if is_active not in (0, 1):
        return False, "Le statut doit être Actif (1) ou Inactif (0)."
    return True, ""

# --- DB UTILS ---
def get_db_conn():
    return sqlite3.connect(DB_PATH)

# --- CRUD ---
def get_all_users():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role, is_active, email FROM users ORDER BY id ASC")
    users = cur.fetchall()
    conn.close()
    return users

def get_user_by_username(username):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()
    return user

def get_user_by_email(email):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cur.fetchone()
    conn.close()
    return user

def add_user(username, password, role, is_active, email):
    # Vérifier que tous les champs sont fournis
    if not all([username, password, role, email]):
        return False, "Tous les champs sont requis, y compris le mot de passe."
    
    # Validations
    ok, msg = validate_username(username)
    if not ok:
        return False, msg
        
    ok, msg = validate_password(password)
    if not ok:
        return False, msg
        
    ok, msg = validate_role(role)
    if not ok:
        return False, msg
        
    ok, msg = validate_is_active(is_active)
    if not ok:
        return False, msg
        
    ok, msg = validate_email(email)
    if not ok:
        return False, msg

    # Vérifier l'unicité
    if get_user_by_username(username):
        return False, "Ce nom d'utilisateur existe déjà."
    if get_user_by_email(email):
        return False, "Cette adresse email est déjà utilisée."

    # Hacher le mot de passe
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (username, password, role, is_active, email)
            VALUES (?, ?, ?, ?, ?)
        """, (username, hashed, role, is_active, email))
        conn.commit()
        conn.close()
        return True, "Utilisateur ajouté avec succès."
    except sqlite3.IntegrityError:
        return False, "Erreur d'intégrité : doublon ou contrainte non respectée."
    except Exception as e:
        return False, f"Erreur lors de l'ajout : {str(e)}"

def update_user(user_id, fields_to_update):
    allowed_fields = {"username", "password", "role", "is_active", "email"}
    sets = []
    values = []

    # Validation username si modifié
    if "username" in fields_to_update:
        ok, msg = validate_username(fields_to_update["username"])
        if not ok:
            return False, msg
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = ? AND id != ?", 
                   (fields_to_update["username"], user_id))
        if cur.fetchone():
            conn.close()
            return False, "Ce nom d'utilisateur existe déjà."
        conn.close()

    # Validation email si modifié
    if "email" in fields_to_update:
        ok, msg = validate_email(fields_to_update["email"])
        if not ok:
            return False, msg
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = ? AND id != ?", 
                   (fields_to_update["email"], user_id))
        if cur.fetchone():
            conn.close()
            return False, "Cette adresse email est déjà utilisée."
        conn.close()

    # Hachage password si modifié
    if "password" in fields_to_update and fields_to_update["password"]:
        ok, msg = validate_password(fields_to_update["password"])
        if not ok:
            return False, msg
        fields_to_update["password"] = bcrypt.hashpw(
            fields_to_update["password"].encode(), 
            bcrypt.gensalt()
        )

    # Validation role si modifié
    if "role" in fields_to_update:
        ok, msg = validate_role(fields_to_update["role"])
        if not ok:
            return False, msg

    # Validation statut si modifié
    if "is_active" in fields_to_update:
        ok, msg = validate_is_active(fields_to_update["is_active"])
        if not ok:
            return False, msg

    # Préparation des champs à mettre à jour
    for k, v in fields_to_update.items():
        if k in allowed_fields:
            sets.append(f"{k} = ?")
            values.append(v)

    if not sets:
        return False, "Aucune donnée à mettre à jour."

    values.append(user_id)

    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET {', '.join(sets)} WHERE id = ?", tuple(values))
        conn.commit()
        conn.close()
        return True, "Utilisateur modifié avec succès."
    except sqlite3.IntegrityError:
        return False, "Erreur d'intégrité : doublon ou contrainte non respectée."
    except Exception as e:
        return False, f"Erreur lors de la mise à jour : {str(e)}"

def delete_user(user_id, current_admin_id):
    if user_id == current_admin_id:
        return False, "Vous ne pouvez pas supprimer votre propre compte."
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True, "Utilisateur supprimé avec succès."
    except Exception as e:
        return False, f"Erreur lors de la suppression : {str(e)}"