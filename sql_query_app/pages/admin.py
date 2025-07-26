import streamlit as st
import pandas as pd
from modules import user_manager, auth

# Configuration de la page
st.set_page_config(page_title="👤 Gestion des utilisateurs")

# Authentification requise
auth.require_login()

# Vérification du rôle
if st.session_state.get("role") != "Admin":
    st.error("Accès non autorisé")
    st.stop()

# Lecture des paramètres d'action
action = st.query_params.get("action", "")
user_id = st.query_params.get("id", "")

# Titre et bouton de déconnexion
st.title("👤 Gestion des utilisateurs")
auth.logout_button()

# ========================
# FORMULAIRE AJOUT / ÉDITION
# ========================
if action in ("add", "edit"):
    is_edit = action == "edit"
    st.subheader("✏️ Modifier un utilisateur" if is_edit else "➕ Ajouter un utilisateur")

    # Valeurs par défaut
    if is_edit:
        if not user_id:
            st.error("ID utilisateur manquant.")
            st.stop()

        user = next((u for u in user_manager.get_all_users() if str(u[0]) == str(user_id)), None)
        if not user:
            st.error("Utilisateur introuvable.")
            st.stop()

        default_username = user[1]
        default_role = user[2]
        default_active = user[3]
    else:
        default_username = ""
        default_role = "Utilisateur"
        default_active = 1

    # Formulaire
    with st.form("user_form"):
        username = st.text_input("Nom d'utilisateur", value=default_username)
        password = st.text_input("Mot de passe", type="password", placeholder="(laisser vide si inchangé)")
        role = st.selectbox("Rôle", ["Admin", "Analyste", "Utilisateur"],
                            index=["Admin", "Analyste", "Utilisateur"].index(default_role))
        actif = st.selectbox("Statut", ["Actif", "Inactif"], index=0 if default_active == 1 else 1)

        col1, col2 = st.columns(2)
        submit = col1.form_submit_button("✅ Enregistrer")
        cancel = col2.form_submit_button("⬅ Annuler")

        if cancel:
            st.query_params.clear()
            st.rerun()

        if submit:
            fields = {
                "username": username,
                "role": role,
                "is_active": 1 if actif == "Actif" else 0
            }
            if password:
                fields["password"] = password

            if is_edit:
                ok, msg = user_manager.update_user(int(user_id), fields)
            else:
                ok, msg = user_manager.add_user(**fields)

            if ok:
                st.success(msg or "Utilisateur enregistré.")
                st.query_params.clear()
                st.rerun()
            else:
                st.error(msg or "Une erreur est survenue.")

# ========================
# MODE LISTE DES UTILISATEURS
# ========================
else:
    if st.button("➕ Ajouter un utilisateur"):
        st.query_params.clear()
        st.query_params.update({"action": "add"})
        st.rerun()

    users = user_manager.get_all_users()
    df = pd.DataFrame(users, columns=["ID", "Nom d'utilisateur", "Rôle", "Actif"])
    df["Actif"] = df["Actif"].map({1: "✅", 0: "❌"})

    st.subheader("📋 Liste des utilisateurs")

    for _, row in df.iterrows():
        col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 2, 1, 1, 1])

        col1.write(f"ID: {row['ID']}")
        col2.write(row["Nom d'utilisateur"])
        col3.write(row["Rôle"])
        col4.write(row["Actif"])

        if col5.button("✏️", key=f"edit_{row['ID']}"):
            st.query_params.clear()
            st.query_params.update({"action": "edit", "id": str(row["ID"])})
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
                    st.error(f"Erreur : {msg}")
