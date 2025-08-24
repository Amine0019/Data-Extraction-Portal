import streamlit as st
import pandas as pd
from modules import user_manager, auth

# Configuration de la page
st.set_page_config(page_title="👤 Gestion des utilisateurs")

# Authentification requise
auth.require_login()

if st.session_state.get("role") != "Admin":
    st.error("Accès non autorisé")
    st.stop()

# Initialisation de l'état global
if "user_mode" not in st.session_state:
    st.session_state.user_mode = None  # valeurs : None, "add", "edit"
if "edit_user_id" not in st.session_state:
    st.session_state.edit_user_id = None
if "search_query" not in st.session_state:
    st.session_state.search_query = ""  # Nouvel état pour la recherche

st.title("👤 Gestion des utilisateurs")
auth.logout_button()

# --- FORMULAIRE D'AJOUT / MODIFICATION ---
if st.session_state.user_mode in ("add", "edit"):
    is_edit = st.session_state.user_mode == "edit"
    st.subheader("✏️ Modifier un utilisateur" if is_edit else "➕ Ajouter un utilisateur")

    # Valeurs par défaut
    if is_edit:
        user_id = st.session_state.edit_user_id
        user = next((u for u in user_manager.get_all_users() if u[0] == user_id), None)
        if not user:
            st.error("Utilisateur introuvable.")
            st.session_state.user_mode = None
            st.stop()
        default_username = user[1]
        default_email = user[4]  # Récupération de l'email
        default_role = user[2]
        default_active = user[3]
    else:
        default_username = ""
        default_email = ""
        default_role = "Utilisateur"
        default_active = 1

    with st.form("user_form", clear_on_submit=False):
        username = st.text_input("Nom d'utilisateur", value=default_username)
        email = st.text_input("Adresse email", value=default_email)  # Champ email ajouté
        password = st.text_input("Mot de passe", type="password", placeholder="(laisser vide si inchangé)")
        role = st.selectbox("Rôle", ["Admin", "Analyste", "Utilisateur"],
                            index=["Admin", "Analyste", "Utilisateur"].index(default_role))
        actif = st.selectbox("Statut", ["Actif", "Inactif"], index=0 if default_active == 1 else 1)

        submitted = st.form_submit_button("✅ Enregistrer")
        cancelled = st.form_submit_button("❌ Annuler")

        if cancelled:
            st.session_state.user_mode = None
            st.session_state.edit_user_id = None
            st.rerun()

        if submitted:
            fields = {
                "username": username,
                "email": email,  # Email ajouté aux champs
                "role": role,
                "is_active": 1 if actif == "Actif" else 0
            }
            if password:
                fields["password"] = password

            if is_edit:
                ok, msg = user_manager.update_user(user_id, fields)
            else:
                # Vérification du mot de passe en mode ajout
                if not password:
                    st.error("Le mot de passe est requis pour créer un nouvel utilisateur.")
                    st.stop()
                
                # Appel correct avec tous les paramètres requis
                ok, msg = user_manager.add_user(
                    username=fields["username"],
                    password=fields["password"],
                    role=fields["role"],
                    is_active=fields["is_active"],
                    email=fields["email"]
                )

            if ok:
                st.success(msg)
                st.session_state.user_mode = None
                st.session_state.edit_user_id = None
                st.rerun()
            else:
                st.error(msg)

# --- BOUTON "AJOUTER UN UTILISATEUR" ---
if st.session_state.user_mode is None:
    if st.button("➕ Ajouter un utilisateur"):
        st.session_state.user_mode = "add"
        st.rerun()

# --- LISTE DES UTILISATEURS ---
if st.session_state.user_mode is None:
    users = user_manager.get_all_users()
    
    # Ajout de la barre de recherche
    search_col1, search_col2 = st.columns([5, 1])
    with search_col1:
        search_query = st.text_input(
            "🔍 Rechercher par nom d'utilisateur",
            value=st.session_state.search_query,
            placeholder="Entrez le nom d'un utilisateur..."
        )
    
    with search_col2:
        st.write("")  # Espace vide pour l'alignement vertical
        st.write("")  # Espace vide pour l'alignement vertical
        if st.button("🗑️ Effacer", use_container_width=True):
            st.session_state.search_query = ""
            st.rerun()
    
    # Mettre à jour la requête de recherche dans l'état de session
    if search_query != st.session_state.search_query:
        st.session_state.search_query = search_query
        st.rerun()
    
    # Filtrer les utilisateurs basés sur la recherche
    if st.session_state.search_query:
        filtered_users = [
            user for user in users 
            if st.session_state.search_query.lower() in user[1].lower()
        ]
        st.info(f"{len(filtered_users)} utilisateur(s) trouvé(s) pour '{st.session_state.search_query}'")
    else:
        filtered_users = users
    
    if not filtered_users:
        st.warning("Aucun utilisateur ne correspond à votre recherche")
    else:
        # Création du DataFrame avec les utilisateurs filtrés
        df = pd.DataFrame(filtered_users, columns=["ID", "Nom d'utilisateur", "Rôle", "Actif", "Email"])
        df["Actif"] = df["Actif"].map({1: "✅", 0: "❌"})

        st.subheader("📋 Liste des utilisateurs")
        
        # Ajout d'une colonne pour l'affichage de l'email
        for _, row in df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 1, 2, 1, 1])

            col1.write(row["Nom d'utilisateur"])
            col2.write(row["Rôle"])
            col3.write(row["Actif"])
            col4.write(row["Email"])  # Affichage de l'email

            if col5.button("✏️", key=f"edit_{row['ID']}"):
                st.session_state.user_mode = "edit"
                st.session_state.edit_user_id = row["ID"]
                st.rerun()

            if col6.button("🗑", key=f"delete_{row['ID']}"):
                if row["ID"] == st.session_state["user_id"]:
                    st.warning("Impossible de supprimer votre propre compte.")
                else:
                    ok, msg = user_manager.delete_user(row["ID"], st.session_state["user_id"])
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)