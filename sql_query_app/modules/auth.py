import streamlit as st
import sqlite3
import bcrypt
import os
import pickle
import time
import datetime

SESSION_FILE = "session_state.pkl"

TIMEOUT_MINUTES = 10  # Durée d'inactivité avant déconnexion automatique

SESSION_EXPIRED_FLAG = "session_expired_flag.pkl"

def get_db_conn():
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'app.db')
    return sqlite3.connect(DB_PATH)

def authenticate(username, password):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password, role, is_active FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()
    if user:
        user_id, username_db, password_hash, role, is_active = user
        if not is_active:
            return None, "Compte inactif. Contactez l'administrateur."
        if bcrypt.checkpw(password.encode(), password_hash):
            return {"user_id": user_id, "username": username_db, "role": role}, None
        else:
            return None, "Mot de passe incorrect."
    else:
        return None, "Nom d'utilisateur inconnu."

def redirect_by_role():
    role = st.session_state.get("role")
    if role == "Admin":
        st.switch_page("pages/admin.py")
    elif role == "Analyste":
        st.switch_page("pages/analyst.py")
    elif role == "Utilisateur":
        st.switch_page("pages/user.py")
    else:
        st.error("Rôle inconnu ou non authentifié.")
        st.stop()

def save_session():
    with open(SESSION_FILE, "wb") as f:
        pickle.dump({
            "authenticated": st.session_state.get("authenticated", False),
            "username": st.session_state.get("username"),
            "user_id": st.session_state.get("user_id"),
            "role": st.session_state.get("role")
        }, f)

def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "rb") as f:
            data = pickle.load(f)
            st.session_state["authenticated"] = data.get("authenticated", False)
            st.session_state["username"] = data.get("username")
            st.session_state["user_id"] = data.get("user_id")
            st.session_state["role"] = data.get("role")

def login_form():
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {display: none !important;}
        </style>
    """, unsafe_allow_html=True)
    st.title("Bienvenue – Identifiez‑vous")
    with st.form("login_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter")
    error = None
    if submitted:
        user, error = authenticate(username, password)
        if user:
            st.session_state["authenticated"] = True
            st.session_state["username"] = user["username"]
            st.session_state["user_id"] = user["user_id"]
            st.session_state["role"] = user["role"]
            save_session()
            redirect_by_role()
    if error:
        st.error(error)

# --- Gestion du timeout d'inactivité ---
def check_session_timeout():
    now = datetime.datetime.now()
    last = st.session_state.get("last_interaction_time")
    if last:
        try:
            last_dt = datetime.datetime.fromisoformat(last)
        except Exception:
            last_dt = now
        elapsed = (now - last_dt).total_seconds() / 60
        if elapsed > TIMEOUT_MINUTES:
            # Déconnexion automatique
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE)
            st.session_state.clear()
            # On pose un flag pour afficher le message sur la page de login
            with open(SESSION_EXPIRED_FLAG, "w") as f:
                f.write("expired")
            st.rerun()
    # Mise à jour de l'horodatage à chaque interaction
    st.session_state["last_interaction_time"] = now.isoformat()

# Affiche le message d'expiration uniquement si le flag existe (timeout réel)
def show_expired_message():
    if os.path.exists(SESSION_EXPIRED_FLAG):
        st.warning("Votre session a expiré pour cause d'inactivité.")
        os.remove(SESSION_EXPIRED_FLAG)

# --- Authentification et login sécurisé ---
def require_login():
    check_session_timeout()
    if not st.session_state.get("authenticated"):
        show_expired_message()
        login_form()
        st.stop()

# --- Déconnexion manuelle sécurisée ---
def logout_button():
    st.sidebar.markdown(f"**Connecté en tant que :** {st.session_state.get('username', '')}")
    if st.sidebar.button("🔓 Se déconnecter"):
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        # On supprime aussi le flag d'expiration pour ne pas afficher le message à tort
        if os.path.exists(SESSION_EXPIRED_FLAG):
            os.remove(SESSION_EXPIRED_FLAG)
        st.success("✅ Déconnexion réussie")
        time.sleep(1)
        st.session_state.clear()
        st.rerun()
