import streamlit as st
from modules.auth import require_login, logout_button, load_session

load_session()

st.set_page_config(initial_sidebar_state="expanded", page_title="Accueil")

require_login()

role = st.session_state.get("role")

# Construction de la sidebar conditionnelle
st.sidebar.title("Navigation")
pages = {"Accueil": "main.py"}
if role == "Admin":
    pages["Admin"] = "pages/admin.py"
elif role == "Analyste":
    pages["Analyste"] = "pages/analyst.py"
elif role == "Utilisateur":
    pages["Utilisateur"] = "pages/user.py"

# Sélecteur de page (main toujours visible)
page_names = list(pages.keys())
selected = st.sidebar.selectbox("Aller à la page :", page_names, index=0)

logout_button()

# Redirection si une page autre que main est choisie
if selected != "Accueil":
    st.switch_page(pages[selected])

st.title(" Data Extraction Portal ")
st.info(f"Bienvenue, {st.session_state.get('username', '')} (rôle : {role})")

st.write("""
Ce portail vous permet d'accéder à l'interface correspondant à votre rôle. Utilisez la barre latérale pour naviguer.
""")