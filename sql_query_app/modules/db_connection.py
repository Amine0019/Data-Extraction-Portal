import pyodbc
import sqlite3
import os

def get_connection_info_from_sqlite(conn_id):
    conn = sqlite3.connect(os.path.join("db", "app.db"))
    cursor = conn.cursor()
    cursor.execute("SELECT type, host, port, db_service, user, password FROM db_connections WHERE id = ?", (conn_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "type": row[0],  # 'SQLServer'
            "host": row[1],
            "port": row[2],
            "db_service": row[3],
            "user": row[4],
            "password": row[5],
            "driver": "ODBC Driver 17 for SQL Server"
        }
    return None

class DatabaseConnection:
    def __init__(self, conn_info):
        try:
            if conn_info["type"].lower() == "sqlserver":
                if conn_info["user"] == "" and conn_info["password"] == "":
                    # 🔒 Authentification Windows
                    conn_str = (
                        f"DRIVER={{{conn_info['driver']}}};"
                        f"SERVER={conn_info['host']},{conn_info['port']};"
                        f"DATABASE={conn_info['db_service']};"
                        f"Trusted_Connection=yes;"
                    )
                else:
                    # 🔐 Authentification SQL Server classique
                    conn_str = (
                        f"DRIVER={{{conn_info['driver']}}};"
                        f"SERVER={conn_info['host']},{conn_info['port']};"
                        f"DATABASE={conn_info['db_service']};"
                        f"UID={conn_info['user']};"
                        f"PWD={conn_info['password']};"
                    )
            else:
                raise ValueError("Type de base non supporté (pour l’instant)")

            self._connection = pyodbc.connect(conn_str)
        except Exception as e:
            self._connection = None
            print("❌ Erreur de connexion :", e)

    def get_connection(self):
        return self._connection


if __name__ == "__main__":
    conn_info = get_connection_info_from_sqlite(1)
    if conn_info:
        db = DatabaseConnection(conn_info)
        conn = db.get_connection()
        if conn:
            print("✅ Connexion réussie à la base de données SQL Server !")
            conn.close()
        else:
            print("❌ Connexion échouée.")
    else:
        print("❌ Connexion introuvable dans db_connections.")
