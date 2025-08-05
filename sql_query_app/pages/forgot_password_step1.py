import sys
import os
# Ajouter le dossier parent au chemin de recherche
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from modules import user_manager
from utils.mail_utils import send_verification_email
import random
import time
from modules.auth import redirect_by_role  # Ajout de l'import pour la redirection

# --- VÉRIFICATION DE CONNEXION ---
if "authenticated" in st.session_state and st.session_state.authenticated:
    st.warning("Vous êtes déjà connecté. Vous ne pouvez pas accéder à cette page.")
    time.sleep(2)
    redirect_by_role()  # Redirection vers la page appropriée
    st.stop()  # Arrêter l'exécution du reste de la page



st.set_page_config(page_title="🔐 Mot de passe oublié - Étape 1")
st.title("🔐 Réinitialiser mon mot de passe - Étape 1")

email = st.text_input("Entrez votre adresse email")

if st.button("Envoyer le code de vérification"):
    user = user_manager.get_user_by_email(email)
    if not user:
        st.error("Aucun compte n'est associé à cet e-mail.")
    else:
        # Générer un code à 6 chiffres
        code = str(random.randint(100000, 999999))
        
        # Stocker dans la session avec timestamp
        st.session_state['reset_email'] = email
        st.session_state['verification_code'] = code
        st.session_state['code_timestamp'] = time.time()
        st.session_state['attempts'] = 0  # Compteur de tentatives
        
        ok, msg = send_verification_email(email, code)
        if ok:
            st.success("Un code de vérification a été envoyé à votre adresse email.")
            st.switch_page("pages/forgot_password_step2.py")
        else:
            st.error(f"Erreur lors de l'envoi de l'e-mail : {msg}")
