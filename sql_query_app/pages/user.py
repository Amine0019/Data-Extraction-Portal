import streamlit as st
from modules import auth

auth.require_login()
if st.session_state.get("role") != "Utilisateur":
    st.error("Accès non autorisé")
    st.stop()

st.set_page_config(page_title="Utilisateur", initial_sidebar_state="expanded")

# Sidebar minimaliste : uniquement cette page
st.sidebar.title("Utilisateur")
st.sidebar.markdown("Espace utilisateur")
auth.logout_button()

st.title("Interface Utilisateur")
st.success(f"Bienvenue, {st.session_state.get('username', '')} (rôle : {st.session_state.get('role', '')})") 