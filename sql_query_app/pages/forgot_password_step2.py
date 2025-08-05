import streamlit as st
from modules import user_manager
import time
import bcrypt

st.set_page_config(page_title="🔐 Mot de passe oublié - Étape 2")
st.title("🔐 Réinitialiser mon mot de passe - Étape 2")

# Vérifier que l'utilisateur vient de l'étape 1
if 'reset_email' not in st.session_state or 'verification_code' not in st.session_state:
    st.error("Veuillez d'abord demander un code de vérification.")
    st.stop()

# Vérifier l'expiration du code (10 minutes)
current_time = time.time()
code_timestamp = st.session_state.get('code_timestamp', 0)
if current_time - code_timestamp > 600:  # 10 minutes en secondes
    st.error("Le code de vérification a expiré. Veuillez recommencer.")
    # Nettoyer toute la session de réinitialisation
    for key in ['reset_email', 'verification_code', 'code_timestamp', 'attempts']:
        st.session_state.pop(key, None)
    st.stop()

# Initialiser le compteur de tentatives
if 'attempts' not in st.session_state:
    st.session_state['attempts'] = 0

# Ajout de conteneurs pour mieux organiser
with st.container():
    code = st.text_input("Entrez le code de vérification reçu par email", placeholder="123456")
    
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        new_password = st.text_input("Nouveau mot de passe", type="password", help="Au moins 8 caractères")
    with col2:
        confirm_password = st.text_input("Confirmer le nouveau mot de passe", type="password")

if st.button("Réinitialiser le mot de passe", type="primary"):
    # Vérifier les tentatives
    if st.session_state['attempts'] >= 3:
        st.error("Trop de tentatives échouées. Veuillez recommencer le processus.")
        # Nettoyer toute la session de réinitialisation
        for key in ['reset_email', 'verification_code', 'code_timestamp', 'attempts']:
            st.session_state.pop(key, None)
        st.stop()
    
    # Validation en cascade
    errors = []
    
    if code != st.session_state['verification_code']:
        errors.append("Code de vérification incorrect.")
        st.session_state['attempts'] += 1
    
    if len(new_password) < 8:
        errors.append("Le mot de passe doit contenir au moins 8 caractères.")
        st.session_state['attempts'] += 1
    
    if new_password != confirm_password:
        errors.append("Les mots de passe ne correspondent pas.")
        st.session_state['attempts'] += 1
    
    if errors:
        for error in errors:
            st.error(error)
        st.stop()
    
    # Tout est valide - réinitialiser le mot de passe
    user = user_manager.get_user_by_email(st.session_state['reset_email'])
    if user:
        # CORRECTION CRITIQUE : Utilisation correcte de bcrypt
        # Générer un nouveau salt et hasher le mot de passe
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), salt)
        
        # Mise à jour dans la base de données
        ok, msg = user_manager.update_user(
            user_id=user[0], 
            fields_to_update={"password": new_password}  # ← mot de passe en clair
        )

        
        if ok:
            st.success("Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter.")
            
            # Nettoyer la session
            for key in ['reset_email', 'verification_code', 'code_timestamp', 'attempts']:
                st.session_state.pop(key, None)
            
            # Ajouter un délai pour une meilleure UX
            time.sleep(2)
            
            # Redirection vers la page de connexion
            st.switch_page("main.py")
        else:
            st.error(f"Erreur lors de la mise à jour : {msg}")
    else:
        st.error("Utilisateur introuvable. Veuillez réessayer.") 