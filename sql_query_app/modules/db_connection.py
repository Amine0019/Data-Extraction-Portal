# modules/db_connection.py

import pyodbc
import threading

class DatabaseConnection:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseConnection, cls).__new__(cls)
                    try:
                        cls._instance._connection = pyodbc.connect(
                            "DRIVER={ODBC Driver 17 for SQL Server};"
                            "SERVER=MOHAMED_AMINE\\SQLEXPRESS;"
                            "DATABASE=DataExtractionPortal;"
                            "Trusted_Connection=yes;"
                        )
                        print("✅ Connexion réussie à la base de données !")
                    except Exception as e:
                        cls._instance._connection = None
                        print("❌ Erreur de connexion :", e)
        return cls._instance

    def get_connection(self):
        return self._connection


# Test de connexion uniquement si exécuté directement
if __name__ == "__main__":
    db = DatabaseConnection()
    conn = db.get_connection()
    if conn:
        print("📦 Connexion prête à être utilisée.")
        conn.close()
    else:
        print("⚠️ Connexion indisponible.")
