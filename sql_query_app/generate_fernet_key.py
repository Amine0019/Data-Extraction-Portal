# generate_fernet_key.py
from cryptography.fernet import Fernet

def main():
    # Générer une nouvelle clé Fernet
    key = Fernet.generate_key()
    
    # Afficher la clé
    print("\n" + "="*50)
    print("Nouvelle clé Fernet générée :")
    print("="*50)
    print(key.decode())
    print("="*50)
    print("\nCopiez cette clé et ajoutez-la à votre fichier .env comme :")
    print("FERNET_KEY=votre_clé_ici")
    print("="*50)

if __name__ == "__main__":
    main()