import sqlite3
from typing import List, Dict, Any, Optional
import os
import re
from pathlib import Path

# ==========================
# CONFIGURATION BASE DE DONNÉES
# ==========================
# Chemin absolu vers la base SQLite
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)  # Crée le dossier si nécessaire
DB_PATH = str(DB_DIR / "app.db")

# ==========================
# INITIALISATION DE LA BASE
# ==========================
def init_db():
    """Initialise la base de données avec les tables nécessaires"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Table db_connections
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS db_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                db_service TEXT NOT NULL,
                user TEXT NOT NULL,
                password TEXT NOT NULL
            )
        """)
        
        # Table queries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sql_text TEXT NOT NULL,
                parameters TEXT,
                roles TEXT,
                db_id INTEGER
            )
        """)
        conn.commit()
    print(f"Base de données initialisée: {DB_PATH}")

# Initialiser la base au premier chargement
if not os.path.exists(DB_PATH):
    init_db()

# ==========================
# CONNEXION SQLITE
# ==========================
def get_connection():
    """Retourne un objet connexion SQLite vers la base locale."""
    return sqlite3.connect(DB_PATH)

# ==========================
# OUTILS POUR DB_CONNECTIONS
# ==========================
def get_all_db_connections() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row  # Active l'accès par nom de colonne
        cur = conn.cursor()
        cur.execute("SELECT id, name, type as db_type FROM db_connections ORDER BY name ASC")
        return [dict(row) for row in cur.fetchall()]  # Conversion explicite

# ==========================
# VALIDATION SQL
# ==========================
def validate_sql(sql_text: str) -> bool:
    """
    Vérifie que le SQL fourni ne contient pas d'instructions dangereuses.

    Interdit :
    - DROP TABLE
    - DROP DATABASE
    - ALTER DATABASE
    - DELETE sans WHERE
    - UPDATE sans WHERE

    Retourne True si valide, False si interdit.
    """
    # Supprimer les commentaires pour éviter les faux positifs
    cleaned_sql = re.sub(r'(--.*)|(/\*[\s\S]*?\*/)', '', sql_text)
    
    forbidden_patterns = [
        r"\bDROP\s+TABLE\b",
        r"\bDROP\s+DATABASE\b",
        r"\bALTER\s+DATABASE\b",
        r"\bTRUNCATE\s+TABLE\b",
        r"\bDELETE\s+FROM\s+\w+\s*(?!(WHERE|LIMIT|ORDER|GROUP|HAVING))",
        r"\bUPDATE\s+\w+\s+SET\s+\w+\s*=\s*.+\s*(?!(WHERE|LIMIT|ORDER|GROUP|HAVING))"
    ]
    
    for pattern in forbidden_patterns:
        if re.search(pattern, cleaned_sql, re.IGNORECASE):
            return False
    
    # Vérification supplémentaire pour DELETE/UPDATE sans clause WHERE
    if re.search(r"\bDELETE\s+FROM\s+\w+;?\s*$", cleaned_sql, re.IGNORECASE):
        return False
        
    if re.search(r"\bUPDATE\s+\w+\s+SET\s+.+;?\s*$", cleaned_sql, re.IGNORECASE) and \
       not re.search(r"\bWHERE\b", cleaned_sql, re.IGNORECASE):
        return False
        
    return True


# ==========================
# VALIDATION DES PARAMÈTRES
# ==========================
def validate_parameters(parameters: str) -> bool:
    """
    Valide le format de la chaîne des paramètres.
    Format attendu : "nom1:type1,nom2:type2"
    Types autorisés : string, int, float, bool, date
    
    Retourne True si valide, False sinon.
    """
    if not parameters.strip():
        return True  # Aucun paramètre est acceptable
    
    valid_types = {"string", "int", "float", "bool", "date"}
    parts = [p.strip() for p in parameters.split(',') if p.strip()]
    
    for part in parts:
        if ':' not in part:
            return False
        
        # Séparation en nom et type
        split_part = part.split(':', 1)
        if len(split_part) != 2:
            return False
            
        name, ptype = split_part
        name = name.strip()
        ptype = ptype.strip().lower()
        
        if not name or not ptype or ptype not in valid_types:
            return False
    
    return True


# ==========================
# CREATE
# ==========================
# ==========================
# CREATE
# ==========================
def add_query(name: str, sql_text: str, parameters: str, roles: str, db_id: int) -> bool:
    """
    Ajoute une nouvelle requête dans la table queries.
    """
    if not name.strip():
        raise ValueError("Le nom de la requête est obligatoire.")
    if not sql_text.strip():
        raise ValueError("Le SQL est obligatoire.")
    if not validate_sql(sql_text):
        raise ValueError("Requête SQL interdite ou non sécurisée.")
    if not validate_parameters(parameters):
        raise ValueError("Format des paramètres invalide. Utilisez: 'nom:type,nom2:type2' avec types: string, int, float, bool, date.")
    if not roles.strip():
        raise ValueError("Les rôles autorisés sont obligatoires.")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO queries (name, sql_text, parameters, roles, db_id)
            VALUES (?, ?, ?, ?, ?)
        """, (name.strip(), sql_text.strip(), parameters.strip(), roles.strip(), db_id))
        conn.commit()
    return True

# ==========================
# READ - Liste toutes les requêtes
# ==========================
def get_all_queries() -> List[Dict[str, Any]]:
    """
    Retourne la liste de toutes les requêtes enregistrées.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, sql_text, parameters, roles, db_id FROM queries")
        rows = cursor.fetchall()
        return [
            {
                "id": r[0],
                "name": r[1],
                "sql_text": r[2],
                "parameters": r[3],
                "roles": r[4],
                "db_id": r[5]
            }
            for r in rows
        ]

# ==========================
# READ - Récupère une requête par ID
# ==========================
def get_query_by_id(query_id: int) -> Optional[Dict[str, Any]]:
    """
    Retourne une requête spécifique en fonction de son ID.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, sql_text, parameters, roles, db_id
            FROM queries
            WHERE id = ?
        """, (query_id,))
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "name": row[1],
                "sql_text": row[2],
                "parameters": row[3],
                "roles": row[4],
                "db_id": row[5]
            }
        return None

# ==========================
# UPDATE
# ==========================
def update_query(query_id: int, name: str, sql_text: str, parameters: str, roles: str, db_id: int) -> bool:
    """
    Met à jour une requête existante.
    """
    if not name.strip():
        raise ValueError("Le nom de la requête est obligatoire.")
    if not sql_text.strip():
        raise ValueError("Le SQL est obligatoire.")
    if not validate_sql(sql_text):
        raise ValueError("Requête SQL interdite ou non sécurisée.")
    if not validate_parameters(parameters):
        raise ValueError("Format des paramètres invalide. Utilisez: 'nom:type,nom2:type2' avec types: string, int, float, bool, date.")
    if not roles.strip():
        raise ValueError("Les rôles autorisés sont obligatoires.")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE queries
            SET name = ?, sql_text = ?, parameters = ?, roles = ?, db_id = ?
            WHERE id = ?
        """, (name.strip(), sql_text.strip(), parameters.strip(), roles.strip(), db_id, query_id))
        conn.commit()
    return cursor.rowcount > 0

# ==========================
# DELETE
# ==========================
def delete_query(query_id: int) -> bool:
    """
    Supprime une requête en fonction de son ID.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM queries WHERE id = ?", (query_id,))
        conn.commit()
    return cursor.rowcount > 0

# ==========================
# TEST
# ==========================
if __name__ == "__main__":
    print(f"Chemin DB: {DB_PATH}")
    print(f"DB existe: {os.path.exists(DB_PATH)}")
    
    # Test de validation des paramètres
    print("\n=== Tests de validation des paramètres ===")
    test_params = [
        ("Valide simple", "age:int"),
        ("Valide multiple", "name:string,age:int"),
        ("Valide types complexes", "start_date:date,is_active:bool"),
        ("Invalide - séparateur incorrect", "start_date:date;end_date"),
        ("Invalide - type manquant", "username"),
        ("Invalide - nom manquant", ":int"),
        ("Invalide - type inconnu", "price:currency"),
    ]
    
    for desc, params in test_params:
        print(f"\nTest: {desc}")
        print(f"Paramètres: '{params}'")
        print(f"Résultat validation: {validate_parameters(params)}")
    
    # Test de création de requête
    try:
        print("\n=== Test d'ajout avec paramètres invalides ===")
        add_query(
            name="Test Paramètres",
            sql_text="SELECT * FROM test",
            parameters="start_date:date;end_date",  # Format invalide
            roles="admin",
            db_id=1
        )
        print("❌ Test d'ajout devrait échouer mais a réussi")
    except ValueError as e:
        print(f"✅ Test d'ajout a échoué comme prévu: {str(e)}")
    
    # Test d'ajout valide
    try:
        print("\n=== Test d'ajout valide ===")
        add_query(
            name="Test Query Valide",
            sql_text="SELECT * FROM sys.tables",
            parameters="is_active:bool,user_id:int",
            roles="admin",
            db_id=1
        )
        print("✅ Test d'ajout valide réussi")
    except Exception as e:
        print(f"❌ Erreur d'ajout valide: {str(e)}")
    
    # Test de récupération
    queries = get_all_queries()
    print(f"\nNombre de requêtes: {len(queries)}")
    if queries:
        last_query = queries[-1]
        print("Dernière requête ajoutée:")
        print(f"Nom: {last_query['name']}")
        print(f"Paramètres: {last_query['parameters']}")
    
    # Test de validation SQL
    valid_sql = "SELECT * FROM users WHERE id = 1"
    invalid_sql = "DROP TABLE users;"
    print(f"\nValidation SQL '{valid_sql}': {validate_sql(valid_sql)}")
    print(f"Validation SQL '{invalid_sql}': {validate_sql(invalid_sql)}")