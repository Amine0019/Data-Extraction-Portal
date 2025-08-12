import streamlit as st
import pandas as pd
from modules.auth import require_login
from modules.db_connection import (
    add_connection, update_connection, delete_connection,
    get_all_connections, get_connection_info, test_connection
)

# Configuration de la page
st.set_page_config(page_title="🔌 Gestion des connexions", layout="wide")

# Authentification requise (admin)
require_login()

if st.session_state.get("role") != "Admin":
    st.error("Accès réservé aux administrateurs")
    st.stop()

# Initialisation de l'état de session
if "connection_mode" not in st.session_state:
    st.session_state.connection_mode = None  # None, "add", "edit"
if "edit_conn_id" not in st.session_state:
    st.session_state.edit_conn_id = None
if "form_data" not in st.session_state:
    st.session_state.form_data = {}

st.title("🔌 Gestion des connexions aux bases de données")

# --- FORMULAIRE D'AJOUT / MODIFICATION ---
if st.session_state.connection_mode in ("add", "edit"):
    is_edit = st.session_state.connection_mode == "edit"
    st.subheader("✏️ Modifier une connexion" if is_edit else "➕ Ajouter une nouvelle connexion")

    # Valeurs par défaut - Correction du type pour le port
    if is_edit:
        connection = get_connection_info(st.session_state.edit_conn_id)
        if not connection:
            st.error("Connexion introuvable.")
            st.session_state.connection_mode = None
            st.stop()
        default_name = connection["name"]
        default_host = connection["host"]
        default_port = int(connection["port"] or 1433)
        default_db_service = connection["db_service"]
        default_user = connection["user"]
        default_password = connection["password"]
        default_type = connection["type"]
    else:
        default_name = ""
        default_host = ""
        default_port = 1433
        default_db_service = ""
        default_user = ""
        default_password = ""
        default_type = "sqlserver"

    with st.form("connection_form", clear_on_submit=False):
        name = st.text_input("Nom de la connexion*", value=default_name)
        conn_type = st.selectbox(
            "Type de base de données*", 
            ["sqlserver"],
            format_func=lambda x: "SQL Server"
        )
        host = st.text_input("Hôte*", value=default_host)
        port = st.number_input("Port*", min_value=1, max_value=65535, value=default_port)
        db_service = st.text_input("Base de données*", value=default_db_service)
        user = st.text_input("Nom d'utilisateur*", value=default_user)
        password = st.text_input("Mot de passe*", type="password", value=default_password)
        
        # Boutons - Correction: utilisation de form_submit_button
        submitted = st.form_submit_button("💾 Enregistrer")
        cancelled = st.form_submit_button("❌ Annuler")

        if cancelled:
            st.session_state.connection_mode = None
            st.session_state.edit_conn_id = None
            st.rerun()

        if submitted:
            if not all([name, host, port, db_service, user, password]):
                st.error("Tous les champs obligatoires (*) doivent être remplis")
            else:
                data = {
                    "name": name,
                    "type": conn_type,
                    "host": host,
                    "port": port,
                    "db_service": db_service,
                    "user": user,
                    "password": password
                }
                
                if is_edit:
                    ok, msg = update_connection(st.session_state.edit_conn_id, data)
                else:
                    ok, msg = add_connection(data)
                
                if ok:
                    st.success(msg)
                    st.session_state.connection_mode = None
                    st.session_state.edit_conn_id = None
                    st.rerun()
                else:
                    st.error(msg)

# --- BOUTON "AJOUTER UNE CONNEXION" ---
if st.session_state.connection_mode is None:
    if st.button("➕ Ajouter une connexion"):
        st.session_state.connection_mode = "add"
        st.rerun()

# --- LISTE DES CONNEXIONS EXISTANTES ---
if st.session_state.connection_mode is None:
    connections = get_all_connections()
    
    if not connections:
        st.info("Aucune connexion configurée")
    else:
        st.subheader("📋 Connexions existantes")
        
        # Création d'un DataFrame pour un affichage tabulaire
        df = pd.DataFrame(connections, columns=["ID", "Nom", "Type", "Hôte", "Port", "Base de données", "Utilisateur"])
        
        for _, row in df.iterrows():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 2, 2, 2, 2, 1, 1])
            
            col1.write(f"**{row['Nom']}**")
            col2.write(f"`{row['Type']}`")
            col3.write(row["Hôte"])
            col4.write(str(row["Port"]))
            col5.write(row["Base de données"])
            col6.write(row["Utilisateur"])
            
            # Bouton Tester
            if col7.button("🧪", key=f"test_{row['ID']}"):
                success, message = test_connection(row['ID'])
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
            
            # Bouton Modifier
            if col7.button("✏️", key=f"edit_{row['ID']}"):
                st.session_state.connection_mode = "edit"
                st.session_state.edit_conn_id = row["ID"]
                st.rerun()
            
            # Bouton Supprimer
            if col7.button("🗑️", key=f"delete_{row['ID']}"):
                ok, msg = delete_connection(row["ID"])
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            
            st.divider()