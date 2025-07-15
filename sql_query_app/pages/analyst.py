import streamlit as st
from modules import auth

auth.require_login()
if st.session_state.get("role") != "Analyste":
    st.error("Accès non autorisé")
    st.stop()

st.set_page_config(page_title="Analyste", initial_sidebar_state="expanded")

auth.logout_button()

st.title("Interface Analyste")
st.success(f"Bienvenue, {st.session_state.get('username', '')} (rôle : {st.session_state.get('role', '')})") 