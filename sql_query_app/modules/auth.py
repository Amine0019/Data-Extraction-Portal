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

        # S'assurer que le hash est bien en bytes
        if isinstance(password_hash, str):
            password_hash = password_hash.encode('utf-8')

        if bcrypt.checkpw(password.encode('utf-8'), password_hash):
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
            "role": st.session_state.get("role"),
            "last_interaction_time": st.session_state.get("last_interaction_time")
        }, f)

def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "rb") as f:
            data = pickle.load(f)
            st.session_state["authenticated"] = data.get("authenticated", False)
            st.session_state["username"] = data.get("username")
            st.session_state["user_id"] = data.get("user_id")
            st.session_state["role"] = data.get("role")
            st.session_state["last_interaction_time"] = data.get("last_interaction_time")

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

        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button("Se connecter")
        with col2:
            forgot_clicked = st.form_submit_button("🔑 Mot de passe oublié ?")

    error = None
    if submitted:
        user, error = authenticate(username, password)
        if user:
            st.session_state.clear()
            st.session_state["authenticated"] = True
            st.session_state["username"] = user["username"]
            st.session_state["user_id"] = user["user_id"]
            st.session_state["role"] = user["role"]
            st.session_state["last_interaction_time"] = datetime.datetime.now().isoformat()
            save_session()
            redirect_by_role()
    elif forgot_clicked:
        # CORRECTION ICI ▼▼▼
        st.switch_page("pages/forgot_password_step1.py")  # Chemin corrigé

    if error:
        st.error(error)


# --- Gestion du timeout d'inactivité ---
def check_session_timeout():
    if not st.session_state.get("authenticated"):
        return  # Pas de timeout si non connecté
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
            with open(SESSION_EXPIRED_FLAG, "w") as f:
                f.write("expired")
            st.rerun()
    # Mise à jour de l'horodatage à chaque interaction
    st.session_state["last_interaction_time"] = now.isoformat()
    save_session()  # Sauvegarde à chaque interaction

# Affiche le message d'expiration uniquement si le flag existe (timeout réel)
def show_expired_message():
    if os.path.exists(SESSION_EXPIRED_FLAG):
        st.warning("Votre session a expiré pour cause d'inactivité.")
        os.remove(SESSION_EXPIRED_FLAG)

# --- Authentification et login sécurisé ---
def require_login():
    # Charger la session si elle existe (au tout début)
    if "authenticated" not in st.session_state:
        load_session()
    # Vérifier le timeout uniquement si authentifié
    if st.session_state.get("authenticated"):
        check_session_timeout()
    # Si non authentifié, afficher login
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
        if os.path.exists(SESSION_EXPIRED_FLAG):
            os.remove(SESSION_EXPIRED_FLAG)
        st.session_state.clear()
        st.success("✅ Déconnexion réussie")
        time.sleep(1)
        st.rerun()
