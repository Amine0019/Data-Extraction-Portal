import pyodbc
import threading
import configparser
import os

class DatabaseConnection:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseConnection, cls).__new__(cls)
                    try:
                        # Lire le fichier config.ini
                        config = configparser.ConfigParser()
                        config.read(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))

                        driver = config['database']['driver']
                        server = config['database']['server']
                        database = config['database']['database']
                        trusted = config['database']['trusted_connection']

                        conn_str = (
                            f"DRIVER={{{driver}}};"
                            f"SERVER={server};"
                            f"DATABASE={database};"
                            f"Trusted_Connection={trusted};"
                        )

                        cls._instance._connection = pyodbc.connect(conn_str)
                    except Exception as e:
                        cls._instance._connection = None
                        print("❌ Erreur de connexion :", e)
        return cls._instance

    def get_connection(self):
        return self._connection


# Test direct
if __name__ == "__main__":
    try:
        db = DatabaseConnection()
        conn = db.get_connection()
        if conn:
            print("✅ Connexion réussie à la base de données !")
            conn.close()
        else:
            print("❌ Erreur de connexion : Aucune instance disponible.")
    except Exception as e:
        print("❌ Erreur de connexion :", e)
