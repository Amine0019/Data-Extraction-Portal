import streamlit as st
import pandas as pd
from modules import user_manager, auth

# Authentification
auth.require_login()
if st.session_state.get("role") != "Admin":
    st.error("Accès non autorisé")
    st.stop()

st.set_page_config(page_title="Admin - Gestion des utilisateurs", initial_sidebar_state="expanded")

auth.logout_button()
st.title("👤 Gestion des utilisateurs")

# Charger les utilisateurs
users = user_manager.get_all_users()
df = pd.DataFrame(users, columns=["ID", "Nom d'utilisateur", "Rôle", "Actif"])

# Interface - Ajout d'un utilisateur
with st.expander("➕ Ajouter un nouvel utilisateur", expanded=False):
    with st.form("add_user_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        role = st.selectbox("Rôle", ["Admin", "Analyste", "Utilisateur"])
        is_active_label = st.selectbox("Actif ?", ["is_active", "not_active"])
        is_active = 1 if is_active_label == "is_active" else 0
        submit = st.form_submit_button("Ajouter")
        if submit:
            ok, msg = user_manager.add_user(username, password, role, is_active)
            if ok:
                st.success(msg or "Utilisateur ajouté.")
                st.rerun()
            else:
                st.error(msg or "Erreur inconnue")

# Tableau interactif
st.subheader("Liste des utilisateurs")
if not df.empty:
    df["Actif"] = df["Actif"].map({1: "✅", 0: "❌"})

    for index, row in df.iterrows():
        col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 2, 1, 1, 1])
        col1.write(f"ID: {row['ID']}")
        col2.write(row["Nom d'utilisateur"])
        col3.write(row["Rôle"])
        col4.write(row["Actif"])
        if col5.button("✏️", key=f"edit_{row['ID']}"):
            st.session_state["edit_user_id"] = row["ID"]
        if col6.button("🗑", key=f"delete_{row['ID']}"):
            if row["ID"] == st.session_state["user_id"]:
                st.warning("Vous ne pouvez pas supprimer votre propre compte.")
            else:
                ok, msg = user_manager.delete_user(row["ID"], st.session_state["user_id"])
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

# Interface - Modifier un utilisateur
if "edit_user_id" in st.session_state:
    user_id = st.session_state["edit_user_id"]
    user = next((u for u in users if u[0] == user_id), None)
    if user:
        with st.expander(f"✏️ Modifier l'utilisateur {user[1]}", expanded=True):
            with st.form("edit_user_form"):
                new_username = st.text_input("Nom d'utilisateur", value=user[1])
                new_password = st.text_input("Nouveau mot de passe (laisser vide pour inchangé)", type="password")
                new_role = st.selectbox("Rôle", ["Admin", "Analyste", "Utilisateur"], index=["Admin", "Analyste", "Utilisateur"].index(user[2]))
                actif_label = st.selectbox("Actif ?", ["is_active", "not_active"], index=0 if user[3] == 1 else 1)
                new_is_active = 1 if actif_label == "is_active" else 0
                save = st.form_submit_button("Enregistrer les modifications")
                if save:
                    fields = {"username": new_username, "role": new_role, "is_active": new_is_active}
                    if new_password:
                        fields["password"] = new_password
                    ok, msg = user_manager.update_user(user_id, fields)
                    if ok:
                        st.success(msg or "Utilisateur modifié.")
                        del st.session_state["edit_user_id"]
                        st.rerun()
                    else:
                        st.error(msg or "Erreur lors de la mise à jour.")
    else:
        st.error("Utilisateur introuvable.")
