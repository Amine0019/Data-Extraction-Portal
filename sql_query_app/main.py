import streamlit as st
from modules.auth import require_login, logout_button, load_session
from dotenv import load_dotenv
import os

# Charger les variables d'environnement dès le démarrage
load_dotenv()

load_session()

st.set_page_config(initial_sidebar_state="expanded", page_title="Accueil")

require_login()

role = st.session_state.get("role")

# Vérification de la clé Fernet (optionnel mais utile pour le debug)
if not os.getenv("FERNET_KEY"):
    print("⚠️ ATTENTION: La clé Fernet n'est pas définie dans .env")

# Construction de la sidebar conditionnelle
st.sidebar.title("Navigation")

# SUPPRIMÉ: Le sélecteur de page et la logique de redirection

logout_button()

st.title(" Data Extraction Portal ")
st.info(f"Bienvenue, {st.session_state.get('username', '')} (rôle : {role})")

st.write("""
Ce portail vous permet d'accéder à l'interface correspondant à votre rôle. Utilisez la barre latérale pour naviguer.
""")