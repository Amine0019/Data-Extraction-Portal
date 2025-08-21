import pyodbc
import pandas as pd
import streamlit as st
from modules import query_manager, db_connection
import re
from typing import List, Dict, Any, Optional

# ==============================
# Charger les requêtes selon le rôle et la base de données
# ==============================
def get_queries_by_db_and_role(db_id: int, role: str) -> List[Dict[str, Any]]:
    """
    Retourne la liste des requêtes accessibles pour une base de données et un rôle donné
    """
    all_queries = query_manager.get_all_queries()
    
    if role == "Admin":
        # Pour les admins, toutes les requêtes de la base sélectionnée
        return [q for q in all_queries if q["db_id"] == db_id]
    
    # Pour les autres rôles, filtrer par rôle ET base de données
    role_lower = role.lower()
    return [q for q in all_queries 
            if q["db_id"] == db_id 
            and role_lower in [r.strip().lower() for r in q["roles"].split(",")]]

# ==============================
# Préparer les champs dynamiques
# ==============================
def get_query_parameters(query: dict) -> List[str]:
    """
    Transforme les paramètres d'une requête en liste utilisable
    Exemple: "start_date:date,end_date:date" → ["start_date", "end_date"]
    """
    if not query["parameters"] or not query["parameters"].strip():
        return []
    
    # Extraire seulement les noms des paramètres (avant le :)
    parameters = []
    for param in query["parameters"].split(','):
        param = param.strip()
        if ':' in param:
            param_name = param.split(':')[0].strip()
            parameters.append(param_name)
        else:
            # Fallback si le format n'est pas respecté
            parameters.append(param)
    
    return parameters

# ==============================
# Exécuter une requête
# ==============================
def execute_query(query: dict, params: dict) -> Optional[pd.DataFrame]:
    """
    Exécute la requête SQL prédéfinie avec pyodbc et retourne un DataFrame
    """
    try:
        # 1️⃣ Récupérer la connexion
        db_info = db_connection.get_connection_by_id(query["db_id"])
        if not db_info:
            st.error("Connexion introuvable en base.")
            return None

        # Déchiffrer le mot de passe
        try:
            db_info["password"] = db_connection.decrypt_password(db_info["password"])
        except Exception as e:
            st.error(f"Erreur de déchiffrement du mot de passe: {str(e)}")
            return None

        # 2️⃣ Établir la connexion
        # Utiliser la classe DatabaseConnection de db_connection
        db = db_connection.DatabaseConnection(db_info)
        conn = db.get_connection()
        
        if not conn:
            st.error("Échec de la connexion à la base de données.")
            return None

        cursor = conn.cursor()

        # 3️⃣ Préparer la requête SQL avec paramètres
        sql = query["sql_text"]
        
        # Remplacer les paramètres nommés par des paramètres positionnels
        param_names = get_query_parameters(query)
        for param_name in param_names:
            if param_name in params:
                # Échapper le nom du paramètre pour éviter les conflits
                placeholder = "?"
                sql = re.sub(rf":{param_name}\b", placeholder, sql)
        
        # Préparer les valeurs dans l'ordre d'apparition des paramètres
        values = []
        for param_name in param_names:
            if param_name in params:
                values.append(params[param_name])
            else:
                st.error(f"Paramètre manquant: {param_name}")
                return None
        
        # 4️⃣ Exécuter la requête
        cursor.execute(sql, values)
        
        # Vérifier si c'est une requête qui retourne des résultats
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            df = pd.DataFrame.from_records(rows, columns=columns)
        else:
            # Pour les requêtes qui ne retournent pas de résultats (INSERT, UPDATE, DELETE)
            conn.commit()
            df = pd.DataFrame({"Status": [f"Query executed successfully. {cursor.rowcount} row(s) affected."]})
        
        conn.close()
        return df

    except pyodbc.Error as e:
        st.error(f"Erreur de base de données: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Erreur inattendue: {str(e)}")
        return None

# ==============================
# Export CSV
# ==============================
def export_csv(df: pd.DataFrame) -> bytes:
    """Exporte un DataFrame en CSV"""
    return df.to_csv(index=False, encoding='utf-8').encode('utf-8')

# ==============================
# Export Excel
# ==============================
def export_excel(df: pd.DataFrame) -> bytes:
    """Exporte un DataFrame en Excel"""
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Résultats')
    return output.getvalue()