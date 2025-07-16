import streamlit as st
import sqlite3
import bcrypt
import os
import pickle
import time

SESSION_FILE = "session_state.pkl"

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

def require_login():
    if not st.session_state.get("authenticated"):
        login_form()
        st.stop()

def logout_button():
    st.sidebar.markdown(f"**Connecté en tant que :** {st.session_state.get('username', '')}")
    if st.sidebar.button("🔓 Se déconnecter"):
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        st.success("✅ Déconnexion réussie")
        time.sleep(1)
        st.session_state.clear()
        st.rerun()
