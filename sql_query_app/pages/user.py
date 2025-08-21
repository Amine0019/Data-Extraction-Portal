import streamlit as st
from modules import auth, db_connection
from utils import query_executor
import pandas as pd
from datetime import datetime

# ==============================
# Authentification et sécurité
# ==============================
auth.require_login()
if st.session_state.get("role") != "Utilisateur":
    st.error("Accès non autorisé")
    st.stop()

st.set_page_config(page_title="Utilisateur - Exécution des requêtes", layout="wide", initial_sidebar_state="expanded")
auth.logout_button()

# ==============================
# Interface Utilisateur
# ==============================
st.title("👤 Interface Utilisateur - Exécution des requêtes")
st.success(f"Bienvenue, {st.session_state.get('username', '')} (rôle : {st.session_state.get('role', '')})")

# ==============================
# Chargement des connexions disponibles
# ==============================
connections = db_connection.get_all_connections()

if not connections:
    st.info("Aucune connexion disponible dans le système.")
    st.stop()

# Créer un mapping nom -> ID pour les connexions
connection_map = {conn[1]: conn[0] for conn in connections}  # name -> id

# ==============================
# Sélection de la base de données
# ==============================
st.header("1. Sélection de la base de données")
selected_connection_name = st.selectbox("Choisissez une base de données :", list(connection_map.keys()))
selected_db_id = connection_map[selected_connection_name]

# ==============================
# Chargement des requêtes disponibles
# ==============================
with st.spinner("Chargement des requêtes disponibles..."):
    queries = query_executor.get_queries_by_db_and_role(selected_db_id, "Utilisateur")

if not queries:
    st.info("Aucune requête disponible pour cette base de données. Contactez un administrateur pour plus d'informations.")
    st.stop()

# Mapping nom → requête
query_names = {q["name"]: q for q in queries}
selected_name = st.selectbox("📌 Choisir une requête à exécuter :", list(query_names.keys()))
selected_query = query_names[selected_name]

# Affichage des détails de la requête
with st.expander("📋 Détails de la requête sélectionnée"):
    st.write(f"**SQL:** ```sql\n{selected_query['sql_text']}\n```")
    if selected_query['parameters']:
        st.write(f"**Paramètres requis:** {selected_query['parameters']}")
    st.write(f"**Base de données cible:** ID {selected_query['db_id']}")

# ==============================
# Saisie des paramètres dynamiques
# ==============================
st.subheader("🔧 Paramètres d'exécution")
params = {}
param_list = query_executor.get_query_parameters(selected_query)

if param_list:
    st.info("Veuillez renseigner les valeurs des paramètres requis :")
    
    # Création des champs en fonction du type de paramètre
    for param in param_list:
        param_lower = param.lower()
        
        # Détermination du type de champ en fonction du nom du paramètre
        if any(keyword in param_lower for keyword in ['date', 'jour', 'mois', 'annee', 'time']):
            params[param] = st.date_input(f"📅 {param}:", value=datetime.now().date())
        elif any(keyword in param_lower for keyword in ['id', 'nombre', 'count', 'quantite', 'montant']):
            params[param] = st.number_input(f"🔢 {param}:", value=0, step=1)
        elif any(keyword in param_lower for keyword in ['email', 'mail', 'courriel']):
            params[param] = st.text_input(f"📧 {param}:", placeholder="exemple@domaine.com")
        elif any(keyword in param_lower for keyword in ['nom', 'prenom', 'name', 'utilisateur', 'user']):
            params[param] = st.text_input(f"👤 {param}:", placeholder="Nom complet")
        else:
            params[param] = st.text_input(f"📝 {param}:")
else:
    st.info("Cette requête ne nécessite pas de paramètres.")

# ==============================
# Exécution de la requête
# ==============================
st.subheader("🚀 Exécution")
if st.button("▶️ Exécuter la requête", type="primary", use_container_width=True):
    # Validation des paramètres requis
    if param_list and not all(params.values()):
        st.error("Veuillez renseigner tous les paramètres requis avant d'exécuter la requête.")
    else:
        with st.spinner("Exécution de la requête en cours..."):
            df = query_executor.execute_query(selected_query, params)
            
            if df is not None:
                if not df.empty:
                    st.success(f"✅ Requête exécutée avec succès! {len(df)} ligne(s) retournée(s).")
                    
                    # Affichage des résultats
                    st.dataframe(df, use_container_width=True)
                    
                    # Métriques
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Lignes retournées", len(df))
                    with col2:
                        st.metric("Colonnes", len(df.columns))
                    
                    # Options d'export
                    st.subheader("💾 Export des résultats")
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename_base = f"{selected_name.replace(' ', '_')}_{timestamp}"
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        csv_data = query_executor.export_csv(df)
                        st.download_button(
                            label="Télécharger en CSV",
                            data=csv_data,
                            file_name=f"{filename_base}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    with col2:
                        excel_data = query_executor.export_excel(df)
                        st.download_button(
                            label="Télécharger en Excel",
                            data=excel_data,
                            file_name=f"{filename_base}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                else:
                    st.warning("⚠️ La requête s'est exécutée mais n'a retourné aucun résultat.")
            else:
                st.error("❌ Erreur lors de l'exécution de la requête. Veuillez vérifier les paramètres et réessayer.")

# ==============================
# Section d'aide
# ==============================
with st.expander("❓ Aide et instructions"):
    st.markdown("""
    ### Guide d'utilisation :
    
    1. **Sélectionnez une requête** dans la liste déroulante
    2. **Renseignez les paramètres** si la requête en nécessite
    3. **Cliquez sur 'Exécuter la requête'** pour lancer l'exécution
    4. **Visualisez les résultats** dans le tableau interactif
    5. **Exportez les données** en CSV ou Excel si nécessaire
    
    ### Types de paramètres :
    - 📅 **Dates** : Utilisez le sélecteur de date
    - 🔢 **Numériques** : Saisissez une valeur numérique
    - 📧 **Emails** : Saisissez une adresse email valide
    - 👤 **Textes** : Saisissez du texte libre
    
    ### En cas de problème :
    - Vérifiez que tous les paramètres requis sont renseignés
    - Contactez votre administrateur ou analyste si une requête ne fonctionne pas
    """)