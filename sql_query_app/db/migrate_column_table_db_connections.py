import sqlite3

conn = sqlite3.connect("db/app.db")
cursor = conn.cursor()

# Étape 1 : Renommer l'ancienne table
cursor.execute("ALTER TABLE db_connections RENAME TO db_connections_old")

# Étape 2 : Créer la nouvelle table avec db_service
cursor.execute("""
CREATE TABLE db_connections (
    id INTEGER PRIMARY KEY,
    name TEXT,
    type TEXT,
    host TEXT,
    port TEXT,
    db_service TEXT,
    user TEXT,
    password TEXT
)
""")

# Étape 3 : Copier les données (en remplaçant "db/service" par "db_service")
cursor.execute("""
INSERT INTO db_connections (id, name, type, host, port, db_service, user, password)
SELECT id, name, type, host, port, "db/service", user, password FROM db_connections_old
""")

# Étape 4 : Supprimer l'ancienne table
cursor.execute("DROP TABLE db_connections_old")

conn.commit()
conn.close()

print("✅ Colonne 'db' renommée en 'db_service' avec succès.")
