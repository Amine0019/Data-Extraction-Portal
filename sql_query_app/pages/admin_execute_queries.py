import streamlit as st
from utils import query_executor
import pandas as pd
from datetime import datetime

# ==============================
# Vérification des permissions
# ==============================
if "role" not in st.session_state or st.session_state.role != "Admin":
    st.error("Accès refusé. Réservé aux administrateurs.")
    st.stop()

# ==============================
# Configuration de la page
# ==============================
st.set_page_config(page_title="Administration - Exécution des requêtes", layout="wide")
st.title("⚙️ Exécution des requêtes - Administration")

# ==============================
# Chargement des requêtes
# ==============================
queries = query_executor.get_queries_by_role("Admin")

if not queries:
    st.info("Aucune requête disponible dans le système.")
    st.stop()

# ==============================
# Sélection de la requête
# ==============================
st.header("1. Sélection de la requête")
query_names = {q["name"]: q for q in queries}
selected_name = st.selectbox("Choisissez une requête à exécuter :", list(query_names.keys()))
selected_query = query_names[selected_name]

# Affichage des détails de la requête
with st.expander("📋 Détails de la requête sélectionnée"):
    st.write(f"**ID:** {selected_query['id']}")
    st.write(f"**Nom:** {selected_query['name']}")
    st.write(f"**SQL:** ```sql\n{selected_query['sql_text']}\n```")
    st.write(f"**Paramètres:** {selected_query['parameters'] if selected_query['parameters'] else 'Aucun'}")
    st.write(f"**Rôles autorisés:** {selected_query['roles']}")
    st.write(f"**ID de la base de données:** {selected_query['db_id']}")

# ==============================
# Saisie des paramètres
# ==============================
st.header("2. Paramètres d'exécution")
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
st.header("3. Exécution et résultats")
if st.button("🚀 Exécuter la requête", type="primary", use_container_width=True):
    with st.spinner("Exécution en cours..."):
        df = query_executor.execute_query(selected_query, params)
        
        if df is not None:
            if not df.empty:
                st.success(f"✅ Requête exécutée avec succès! {len(df)} ligne(s) retournée(s).")
                
                # Affichage des résultats
                st.dataframe(df, use_container_width=True)
                
                # Métriques rapides
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Lignes retournées", len(df))
                with col2:
                    st.metric("Colonnes", len(df.columns))
                with col3:
                    st.metric("Taille", f"{df.memory_usage(deep=True).sum() / 1024:.2f} Ko")
                
                # Options d'export
                st.header("4. Export des résultats")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename_base = f"{selected_name.replace(' ', '_')}_{timestamp}"
                
                col1, col2 = st.columns(2)
                with col1:
                    csv_data = query_executor.export_csv(df)
                    st.download_button(
                        label="💾 Télécharger en CSV",
                        data=csv_data,
                        file_name=f"{filename_base}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                with col2:
                    excel_data = query_executor.export_excel(df)
                    st.download_button(
                        label="📊 Télécharger en Excel",
                        data=excel_data,
                        file_name=f"{filename_base}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            else:
                st.warning("⚠️ La requête s'est exécutée mais n'a retourné aucun résultat.")
        else:
            st.error("❌ Erreur lors de l'exécution de la requête. Veuillez vérifier les logs pour plus de détails.")

# ==============================
# Informations de débogage (pour admin)
# ==============================
with st.expander("🐛 Informations de débogage (Admin)"):
    st.write("**Paramètres envoyés:**", params)
    st.write("**Requête sélectionnée:**", selected_query)
    st.write("**Session state:**", {k: v for k, v in st.session_state.items() if k != 'password'})