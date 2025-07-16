# Data Extraction Portal

## Description

Application Python avec le framework Streamlit pour exécuter en sécurité des requêtes SQL prédéfinies sur SQL Server. Interface intuitive pour utilisateurs métier, avec gestion des rôles, authentification sécurisée, journalisation et export des résultats. Idéale en environnement sensible.

## Fonctionnalités principales

- Authentification sécurisée avec gestion des rôles (Admin, Analyste, Utilisateur)
- Exécution de requêtes SQL prédéfinies avec paramètres dynamiques
- Connexion aux bases de données SQL Server via pyodbc
- Journalisation complète des actions utilisateurs (connexion, exécution, erreurs)
- Export facile des résultats en CSV ou Excel
- Interface web intuitive et responsive développée avec Streamlit

## Prérequis

- Python 3.10+
- Modules Python (voir `requirements.txt`):
  - streamlit
  - pyodbc
  - bcrypt
  - pandas
  - openpyxl
- Driver ODBC pour SQL Server installé ODBC Driver 17

## Installation

1. Cloner le dépôt :
   ```bash
   git clone https://github.com/Amine0019/Projet-Data-Extraction-Portal.git
   cd Projet-Data-Extraction-Portal
