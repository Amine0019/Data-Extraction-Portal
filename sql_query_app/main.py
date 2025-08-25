import streamlit as st
from modules.auth import require_login, logout_button, load_session
from dotenv import load_dotenv
import os
import base64
import glob

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

logout_button()

st.title(" Data Extraction Portal ")
st.info(f"Bienvenue, {st.session_state.get('username', '')} (rôle : {role})")

st.write("""
Ce portail vous permet d'accéder à l'interface correspondant à votre rôle. Utilisez la barre latérale pour naviguer.
""")

# Fonction pour créer un lien de téléchargement
def get_binary_file_downloader_html(file_path, file_label='File'):
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        bin_str = base64.b64encode(data).decode()
        file_name = os.path.basename(file_path)
        href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_name}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">📥 {file_label}</a>'
        return href
    except Exception as e:
        st.error(f"Erreur: {str(e)}")
        return None

# Section pour le téléchargement du guide administrateur - réservée aux admins
st.header("Documentation")

# Vérifier si l'utilisateur est Admin avant d'afficher la section de téléchargement
if role == "Admin":
    # Rechercher tous les fichiers PDF dans le répertoire courant
    pdf_files = glob.glob("*.pdf")

    if pdf_files:
        # Prendre le premier fichier PDF trouvé
        pdf_file = pdf_files[0]
        
        # Afficher le nom du fichier pour confirmation
        st.success(f"Guide trouvé: {pdf_file}")
        
        # Créer le lien de téléchargement
        download_link = get_binary_file_downloader_html(pdf_file, "Télécharger le Guide Administrateur")
        
        if download_link:
            st.markdown(download_link, unsafe_allow_html=True)
    else:
        # Afficher le répertoire courant et les fichiers pour le débogage
        current_dir = os.getcwd()
        st.warning(f"Aucun fichier PDF trouvé dans le répertoire: {current_dir}")
        
        # Lister tous les fichiers pour aider au débogage
        all_files = os.listdir()
        st.info(f"Fichiers présents: {', '.join(all_files)}")
        
    st.write("""
    Le guide administrateur contient toutes les instructions détaillées pour utiliser 
    l'application, gérer les utilisateurs, configurer les connexions aux bases de données,
    et exécuter des requêtes prédéfinies.
    """)
else:
    st.info("La documentation administrative est réservée aux utilisateurs ayant le rôle Admin.")