#!/usr/bin/env python3
"""
Script pour générer une clé secrète sécurisée pour PythonAnywhere
À exécuter localement ou sur PythonAnywhere
"""
import secrets
import string

def generate_secret_key(length=32):
    """Génère une clé secrète sécurisée"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    secret = generate_secret_key()
    print("\n" + "="*60)
    print("🔐 Clé Secrète Générée (SECRET_KEY)")
    print("="*60)
    print(f"\n{secret}\n")
    print("Copiez cette clé et collez-la dans votre fichier WSGI")
    print("sur PythonAnywhere dans la variable SECRET_KEY")
    print("="*60 + "\n")
