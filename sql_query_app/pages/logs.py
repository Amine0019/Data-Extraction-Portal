import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta

# ==========================
# Vérification des droits
# ==========================
if "role" not in st.session_state or st.session_state.role != "Admin":
    st.error("Accès refusé. Réservé aux administrateurs.")
    st.stop()

st.title("📜 Journal des activités")

# ==========================
# Configuration
# ==========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db", "app.db")

# ==========================
# Fonctions utilitaires
# ==========================
def get_logs(filter_user=None, filter_status=None, limit=1000):
    """Récupère les logs depuis la base de données"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        query = """
            SELECT id, username, query_id, timestamp, status, message 
            FROM logs 
            WHERE 1=1
        """
        params = []

        if filter_user:
            query += " AND username LIKE ?"
            params.append(f"%{filter_user}%")

        if filter_status and filter_status != "Tous":
            query += " AND status = ?"
            params.append(filter_status)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
        
    except Exception as e:
        st.error(f"Erreur lors de la récupération des logs: {str(e)}")
        return None

def delete_old_logs(days=30):
    """Supprime les logs de plus de X jours"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cutoff_date = datetime.now() - timedelta(days=days)
        cursor.execute("DELETE FROM logs WHERE timestamp < ?", (cutoff_date,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erreur lors de la suppression: {str(e)}")
        return False

def format_timestamp(timestamp_str):
    """Formate un timestamp en une chaîne lisible"""
    if not timestamp_str:
        return "N/A"
    
    # Essayer différents formats de date
    formats = [
        '%Y-%m-%d %H:%M:%S.%f',  # Format avec microsecondes
        '%Y-%m-%d %H:%M:%S',      # Format sans microsecondes
        '%Y-%m-%d %H:%M',         # Format sans secondes
        '%Y-%m-%d'                # Format date seulement
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(timestamp_str, fmt)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue
    
    # Si aucun format ne fonctionne, retourner la valeur originale
    return timestamp_str

# ==========================
# Interface principale
# ==========================
st.header("Filtres de consultation")

# Options de filtrage
col1, col2 = st.columns(2)
with col1:
    user_filter = st.text_input("🔎 Filtrer par utilisateur", "")
with col2:
    status_filter = st.selectbox("Statut", ["Tous", "success", "error"])

# Bouton pour actualiser
if st.button("🔄 Actualiser"):
    st.rerun()

# Récupération des logs
with st.spinner("Chargement des logs..."):
    logs_df = get_logs(
        filter_user=user_filter if user_filter else None,
        filter_status=status_filter if status_filter != "Tous" else None
    )

# Affichage des résultats
if logs_df is not None:
    if not logs_df.empty:
        # Formater les dates
        logs_df['timestamp'] = logs_df['timestamp'].apply(format_timestamp)
        
        # Afficher le nombre de résultats
        st.success(f"{len(logs_df)} logs trouvés")
        
        # Afficher le dataframe
        st.dataframe(logs_df, use_container_width=True)
        
        # Options d'export
        csv = logs_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Exporter en CSV", 
            csv, 
            f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
            "text/csv"
        )
        
        # Option pour effacer les logs anciens
        if st.button("🗑️ Supprimer les logs de plus de 30 jours"):
            if delete_old_logs(30):
                st.success("Logs anciens supprimés avec succès!")
                st.rerun()
            else:
                st.error("Erreur lors de la suppression des logs anciens")
    else:
        st.info("Aucun log trouvé avec les critères sélectionnés.")
else:
    st.error("Erreur lors du chargement des logs. Vérifiez la connexion à la base de données.")