import streamlit as st
import sqlite3
import bcrypt
import os

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

def login_form():
    st.title("Connexion au portail Data Extraction")
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
            st.rerun()
    if error:
        st.error(error)

def require_login(roles=None):
    if not st.session_state.get("authenticated"):
        login_form()
        st.stop()
    if roles:
        if st.session_state.get("role") not in roles:
            st.error("Accès refusé : rôle insuffisant.")
            st.stop()

def logout_button():
    st.sidebar.markdown(f"**Connecté en tant que :** {st.session_state.get('username', '')}")
    if st.sidebar.button("Se déconnecter"):
        st.session_state.clear()
        st.rerun()
