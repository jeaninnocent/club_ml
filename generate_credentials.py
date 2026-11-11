#!/usr/bin/env python3
"""
Générateur de credentials sécurisés pour Vercel
Crée: ADMIN_PASSWORD et SECRET_KEY
"""
import secrets
import string

def generate_strong_password(length=16):
    """Génère un mot de passe fort"""
    # Mélange de caractères sans ambiguïté
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    # Éviter: 0/O, 1/l/I pour éviter les confusions
    chars = chars.replace("0", "").replace("O", "").replace("1", "").replace("l", "").replace("I", "")
    
    password = ''.join(secrets.choice(chars) for _ in range(length))
    return password

def generate_secret_key():
    """Génère une clé secrète hex"""
    return secrets.token_hex(32)

def main():
    print("="*70)
    print("🔐 GÉNÉRATEUR DE CREDENTIALS SÉCURISÉS - VERCEL")
    print("="*70)
    print()
    
    # Générer les credentials
    admin_password = generate_strong_password(20)
    secret_key = generate_secret_key()
    
    print("✅ CREDENTIALS GÉNÉRÉS AVEC SUCCÈS\n")
    
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│ À COPIER-COLLER dans Vercel Settings → Environment Variables│")
    print("└─────────────────────────────────────────────────────────────┘")
    print()
    
    print("1️⃣  ADMIN_PASSWORD:")
    print(f"   {admin_password}")
    print()
    
    print("2️⃣  SECRET_KEY:")
    print(f"   {secret_key}")
    print()
    
    print("3️⃣  ADMIN_USER (déjà configuré):")
    print("   admin")
    print()
    
    print("4️⃣  DB_PATH (déjà configuré):")
    print("   /tmp/club.db")
    print()
    
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│ INSTRUCTIONS:                                               │")
    print("├─────────────────────────────────────────────────────────────┤")
    print("│ 1. Allez sur: https://vercel.com/dashboard                 │")
    print("│ 2. Sélectionnez votre projet                               │")
    print("│ 3. Settings → Environment Variables                        │")
    print("│ 4. Cliquez sur 'Add New'                                   │")
    print("│ 5. Entrez les variables ci-dessus                          │")
    print("│ 6. Redéployez le projet                                    │")
    print("└─────────────────────────────────────────────────────────────┘")
    print()
    
    print("⚠️  IMPORTANT:")
    print("   • Ne commitez JAMAIS ces credentials")
    print("   • Gardez-les en sécurité (pas de email, chat, etc.)")
    print("   • Utilisez UNIQUEMENT les variables Vercel")
    print("   • Changez ADMIN_PASSWORD régulièrement")
    print()
    
    print("📝 Enregistrement des credentials:")
    response = input("   Voulez-vous les enregistrer dans un fichier .env.local? (y/n) ")
    
    if response.lower() == 'y':
        with open(".env.local", "w") as f:
            f.write(f"ADMIN_USER=admin\n")
            f.write(f"ADMIN_PASSWORD={admin_password}\n")
            f.write(f"SECRET_KEY={secret_key}\n")
            f.write(f"DB_PATH=/tmp/club.db\n")
        print("   ✓ Enregistré dans .env.local (NE PAS COMMITTER)")
    
    print()
    print("✅ Tout est prêt pour le déploiement Vercel!")
    print()

if __name__ == "__main__":
    main()
