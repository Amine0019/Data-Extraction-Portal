import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

def send_verification_email(recipient, code):
    msg = EmailMessage()
    msg["Subject"] = "🔐 Code de vérification - Réinitialisation du mot de passe"
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient
    
    msg.set_content(
        f"Bonjour,\n\n"
        f"Voici votre code de vérification : {code}\n\n"
        f"Ce code est valable 10 minutes.\n\n"
        f"Si vous n'avez pas demandé de réinitialisation, ignorez cet email.\n\n"
        f"Cordialement,\n"
        f"L'équipe de support"
    )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        return True, "E-mail envoyé"
    except Exception as e:
        return False, str(e)