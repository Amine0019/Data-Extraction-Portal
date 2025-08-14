import streamlit as st
import pandas as pd
from modules import query_manager, db_connection

# ==========================
# Vérification des droits
# ==========================
if "role" not in st.session_state or st.session_state.role != "Admin":
    st.error("Accès refusé. Réservé aux administrateurs.")
    st.stop()

st.title("⚙️ Administration - Gestion des requêtes prédéfinies")

# Initialisation de l'état de session
if "query_mode" not in st.session_state:
    st.session_state.query_mode = None  # None, "add", "edit"
if "edit_query_id" not in st.session_state:
    st.session_state.edit_query_id = None

# ==========================
# Chargement des données
# ==========================
def load_queries():
    return query_manager.get_all_queries()

def load_databases():
    return db_connection.get_all_connections()

queries = load_queries()
db_list = load_databases()

# --- FORMULAIRE D'AJOUT / MODIFICATION ---
if st.session_state.query_mode in ("add", "edit"):
    is_edit = st.session_state.query_mode == "edit"
    st.subheader("✏️ Modifier une requête" if is_edit else "➕ Ajouter une nouvelle requête")

    # Valeurs par défaut
    if is_edit:
        query = next((q for q in queries if q['id'] == st.session_state.edit_query_id), None)
        if not query:
            st.error("Requête introuvable.")
            st.session_state.query_mode = None
            st.session_state.edit_query_id = None
            st.stop()
        default_name = query["name"]
        default_sql = query["sql_text"]
        default_params = query["parameters"]
        default_roles = query["roles"].split(",") if query["roles"] else []
        default_db_id = query["db_id"]
    else:
        default_name = ""
        default_sql = ""
        default_params = ""
        default_roles = []
        default_db_id = None

    with st.form("query_form", clear_on_submit=False):
        name = st.text_input("Nom de la requête*", value=default_name)
        sql_text = st.text_area("SQL*", value=default_sql, height=150)
        parameters = st.text_input("Paramètres (séparés par des virgules)", value=default_params)
        roles = st.multiselect(
            "Rôles autorisés*",
            ["Admin", "Analyste", "Utilisateur"],
            default=default_roles
        )

        # Préparation de la liste des bases
        db_map = {db[1]: db[0] for db in db_list}  # Index 1=name, 0=id
        db_names = list(db_map.keys())
        
        # Trouver l'index de la base par défaut
        if is_edit and db_list:
            # Trouver le nom de la base actuellement sélectionnée
            current_db_name = next((name for name, id in db_map.items() if id == default_db_id), None)
            if current_db_name:
                default_index = db_names.index(current_db_name)
            else:
                default_index = 0
        else:
            default_index = 0

        if db_list:
            db_name_selected = st.selectbox("Base associée*", db_names, index=default_index)
        else:
            st.warning("⚠️ Aucune base disponible. Ajoutez d'abord une connexion.")
            db_name_selected = None

        # Boutons
        submitted = st.form_submit_button("💾 Enregistrer")
        cancelled = st.form_submit_button("❌ Annuler")

        if cancelled:
            st.session_state.query_mode = None
            st.session_state.edit_query_id = None
            st.rerun()

        if submitted:
            try:
                if not name.strip() or not sql_text.strip() or not roles or not db_name_selected:
                    st.error("Les champs obligatoires (*) doivent être remplis")
                else:
                    if is_edit:
                        success = query_manager.update_query(
                            st.session_state.edit_query_id, name, sql_text, parameters, ",".join(roles), db_map[db_name_selected]
                        )
                        if success:
                            st.success("Requête mise à jour avec succès ✅")
                        else:
                            st.error("Erreur lors de la mise à jour.")
                    else:
                        query_manager.add_query(
                            name, sql_text, parameters, ",".join(roles), db_map[db_name_selected]
                        )
                        st.success("Requête ajoutée avec succès ✅")
                    
                    # Réinitialiser et recharger
                    st.session_state.query_mode = None
                    st.session_state.edit_query_id = None
                    st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")

# --- BOUTON "AJOUTER UNE REQUÊTE" ---
if st.session_state.query_mode is None:
    if st.button("➕ Ajouter une requête"):
        st.session_state.query_mode = "add"
        st.rerun()

# --- LISTE DES REQUÊTES ---
if st.session_state.query_mode is None:
    st.subheader("📜 Liste des requêtes")
    if not queries:
        st.info("Aucune requête enregistrée.")
    else:
        # Affichage sous forme de tableau avec actions
        for q in queries:
            col1, col2, col3 = st.columns([4, 1, 1])
            col1.markdown(f"**{q['name']}** – Base ID: {q['db_id']} – Rôles: {q['roles']}")

            if col2.button("✏️ Modifier", key=f"edit_{q['id']}"):
                st.session_state.query_mode = "edit"
                st.session_state.edit_query_id = q["id"]
                st.rerun()

            if col3.button("🗑️ Supprimer", key=f"delete_{q['id']}"):
                if query_manager.delete_query(q["id"]):
                    st.success(f"Requête '{q['name']}' supprimée ✅")
                    st.rerun()
                else:
                    st.error("Erreur lors de la suppression.")