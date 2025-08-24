# modules/database_logger.py
import sqlite3
import os
import pandas as pd
from datetime import datetime
import streamlit as st

# Chemin absolu pour éviter les problèmes de chemins relatifs
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db", "app.db")

def init_db():
    """Initialise la base de données et crée la table logs si elle n'existe pas"""
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                query_id INTEGER,
                timestamp DATETIME,
                status TEXT,
                message TEXT
            )
        """)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erreur lors de l'initialisation de la base de données: {str(e)}")
        return False

def log_action(username: str, query_id: int, status: str, message: str):
    """
    Enregistre une action dans la table logs
    """
    try:
        # Initialiser la base si elle n'existe pas
        init_db()
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO logs (username, query_id, timestamp, status, message)
            VALUES (?, ?, ?, ?, ?)
        """, (username, query_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status, message))
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Erreur de journalisation: {str(e)}")
        print(f"Erreur de journalisation: {str(e)}")
        return False

def get_logs_simple():
    """
    Version simplifiée pour récupérer les logs - sans filtres
    """
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        
        query = "SELECT id, username, query_id, timestamp, status, message FROM logs ORDER BY timestamp DESC LIMIT 100"
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
        
    except Exception as e:
        st.error(f"Erreur lors de la récupération des logs: {str(e)}")
        return None