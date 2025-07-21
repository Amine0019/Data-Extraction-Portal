import streamlit as st
from modules import user_manager, auth

auth.require_login()
if st.session_state.get("role") != "Admin":
    st.error("Accès non autorisé")
    st.stop()

st.set_page_config(page_title="Admin - Gestion des utilisateurs", initial_sidebar_state="expanded")

auth.logout_button()

st.title("Gestion des utilisateurs")

tab1, tab2, tab3, tab4 = st.tabs(["🔍 Liste", "➕ Ajouter", "✏️ Modifier", "🗑 Supprimer"])

# --- LIRE ---
with tab1:
    users = user_manager.get_all_users()
    import pandas as pd
    df = pd.DataFrame(users, columns=["ID", "Nom d'utilisateur", "Rôle", "Actif"])
    df["Actif"] = df["Actif"].map({1: "is_active", 0: "not_active"})
    st.dataframe(df, use_container_width=True)

# --- AJOUTER ---
with tab2:
    st.subheader("Ajouter un utilisateur")
    with st.form("add_user_form"):
        username = st.text_input("Nom d'utilisateur (lettres et underscore, unique)")
        password = st.text_input("Mot de passe (min. 8 caractères)", type="password")
        role = st.selectbox("Rôle", ["Admin", "Analyste", "Utilisateur"])
        actif_label = st.selectbox("Actif ?", ["is_active", "not_active"])
        is_active = 1 if actif_label == "is_active" else 0
        submitted = st.form_submit_button("Ajouter")
    if submitted:
        ok, msg = user_manager.add_user(username, password, role, is_active)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

# --- MODIFIER ---
with tab3:
    st.subheader("Modifier un utilisateur")
    users = user_manager.get_all_users()
    if users:
        user_dict = {f"{u[1]} (id={u[0]})": u for u in users}
        selected = st.selectbox("Sélectionner un utilisateur à modifier", list(user_dict.keys()), key="mod_select")
        user = user_dict[selected]
        with st.form("edit_user_form"):
            new_username = st.text_input("Nom d'utilisateur", value=user[1])
            new_password = st.text_input("Nouveau mot de passe (laisser vide pour inchangé)", type="password")
            new_role = st.selectbox("Rôle", ["Admin", "Analyste", "Utilisateur"], index=["Admin", "Analyste", "Utilisateur"].index(user[2]))
            actif_label = st.selectbox("Actif ?", ["is_active", "not_active"], index=0 if user[3] == 1 else 1)
            new_is_active = 1 if actif_label == "is_active" else 0
            update_btn = st.form_submit_button("Enregistrer les modifications")
        if update_btn:
            fields = {"username": new_username, "role": new_role, "is_active": new_is_active}
            if new_password:
                fields["password"] = new_password
            ok, msg = user_manager.update_user(user[0], fields)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    else:
        st.info("Aucun utilisateur à afficher.")

# --- SUPPRIMER ---
with tab4:
    st.subheader("Supprimer un utilisateur")
    users = user_manager.get_all_users()
    if users:
        user_dict = {f"{u[1]} (id={u[0]})": u for u in users}
        selected = st.selectbox("Sélectionner un utilisateur à supprimer", list(user_dict.keys()), key="del_select")
        user = user_dict[selected]
        if user[0] == st.session_state["user_id"]:
            st.warning("Vous ne pouvez pas supprimer votre propre compte.")
            st.button("Supprimer", disabled=True, key="del_btn_disabled")
        else:
            if st.button("Supprimer", key=f"delete_{user[0]}"):
                ok, msg = user_manager.delete_user(user[0], st.session_state["user_id"])
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
    else:
        st.info("Aucun utilisateur à afficher.") 