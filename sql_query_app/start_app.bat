@echo off
REM Se déplacer dans le dossier du script
cd /d %~dp0

REM Active l'environnement virtuel Python
call ..\venv\Scripts\activate.bat

REM Lance l'application Streamlit
streamlit run main.py --server.port 8505 --server.address DataExtractionPortal

pause
