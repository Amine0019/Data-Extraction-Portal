import streamlit as st
from modules import user_manager

# --- Contrôle d'accès ---
# if "role" not in st.session_state:
#     st.error("Vous devez être authentifié pour accéder à cette page.")
#     st.stop()
# if st.session_state["role"] != "Admin":
#     st.error("Accès réservé aux administrateurs.")
#     st.stop()

# Pour test sans authentification :
st.session_state["role"] = "Admin"
st.session_state["user_id"] = 1  # ID admin fictif pour test

st.title("Gestion des utilisateurs")

# --- Onglets CRUD ---
tabs = st.tabs(["Liste des utilisateurs", "Ajouter", "Modifier", "Supprimer"])

# --- 1. Lister les utilisateurs ---
with tabs[0]:
    users = user_manager.get_all_users()
    st.subheader("Utilisateurs existants")
    st.dataframe(
        [{"ID": u[0], "Nom d'utilisateur": u[1], "Rôle": u[2], "Actif ?": "is_active" if u[3] else "not_active"} for u in users],
        hide_index=True
    )

# --- 2. Ajouter un utilisateur ---
with tabs[1]:
    st.subheader("Ajouter un utilisateur")
    with st.form("add_user_form"):
        username = st.text_input("Nom d'utilisateur (alphanumérique, unique)")
        password = st.text_input("Mot de passe (min. 8 caractères)", type="password")
        role = st.selectbox("Rôle", ["Admin", "Analyste", "Utilisateur"])
        actif_label = st.selectbox("Actif ?", ["is_active", "not_active"])
        is_active = 1 if actif_label == "is_active" else 0
        submitted = st.form_submit_button("Ajouter")
        if submitted:
            ok, msg = user_manager.add_user(username, password, role, is_active)
            if ok:
                st.success(msg)
                st.experimental_rerun()
            else:
                st.error(msg)

# --- 3. Modifier un utilisateur ---
with tabs[2]:
    st.subheader("Modifier un utilisateur")
    users = user_manager.get_all_users()
    user_choices = {f"{u[1]} (ID {u[0]})": u for u in users}
    if user_choices:
        selected = st.selectbox("Sélectionner un utilisateur", list(user_choices.keys()))
        user = user_choices.get(selected)
        if user:
            with st.form("edit_user_form"):
                new_username = st.text_input("Nom d'utilisateur", value=user[1])
                new_password = st.text_input("Nouveau mot de passe (laisser vide pour ne pas changer)", type="password")
                new_role = st.selectbox("Rôle", ["Admin", "Analyste", "Utilisateur"], index=["Admin", "Analyste", "Utilisateur"].index(user[2]))
                actif_label = st.selectbox("Actif ?", ["is_active", "not_active"], index=0 if user[3] else 1)
                is_active = 1 if actif_label == "is_active" else 0
                submitted = st.form_submit_button("Modifier")
                if submitted:
                    fields = {}
                    if new_username != user[1]:
                        fields["username"] = new_username
                    if new_password:
                        fields["password"] = new_password
                    if new_role != user[2]:
                        fields["role"] = new_role
                    if is_active != user[3]:
                        fields["is_active"] = is_active
                    if not fields:
                        st.info("Aucune modification détectée.")
                    else:
                        ok, msg = user_manager.update_user(user[0], fields)
                        if ok:
                            st.success(msg)
                            st.experimental_rerun()
                        else:
                            st.error(msg)
    else:
        st.info("Aucun utilisateur à modifier.")

# --- 4. Supprimer un utilisateur ---
with tabs[3]:
    st.subheader("Supprimer un utilisateur")
    users = user_manager.get_all_users()
    user_choices = {f"{u[1]} (ID {u[0]})": u for u in users}
    if user_choices:
        selected = st.selectbox("Sélectionner un utilisateur à supprimer", list(user_choices.keys()))
        user = user_choices.get(selected)
        current_admin_id = st.session_state.get("user_id")
        if user:
            if user[0] == current_admin_id:
                st.warning("Vous ne pouvez pas supprimer votre propre compte.")
                st.button("Supprimer", disabled=True)
            else:
                if st.button("Supprimer"):
                    ok, msg = user_manager.delete_user(user[0], current_admin_id)
                    if ok:
                        st.success(msg)
                        st.experimental_rerun()
                    else:
                        st.error(msg)
    else:
        st.info("Aucun utilisateur à supprimer.")
