"""
Script de test pour valider que l'app est prête pour Vercel
"""
import os
import sys

print("🔍 Validation pour déploiement Vercel...\n")

# Vérifications
checks = []

# 1. Fichier api/index.py existe
if os.path.exists("api/index.py"):
    checks.append(("✓", "api/index.py existe"))
else:
    checks.append(("✗", "api/index.py MANQUANT"))
    sys.exit(1)

# 2. vercel.json existe
if os.path.exists("vercel.json"):
    checks.append(("✓", "vercel.json existe"))
else:
    checks.append(("✗", "vercel.json MANQUANT"))

# 3. requirements.txt a les dépendances
with open("requirements.txt", "r") as f:
    reqs = f.read().lower()
    if "flask" in reqs and "werkzeug" in reqs:
        checks.append(("✓", "Dépendances Flask/Werkzeug présentes"))
    else:
        checks.append(("✗", "Dépendances INCOMPLÈTES"))

# 4. app.py existe
if os.path.exists("app.py"):
    checks.append(("✓", "app.py existe"))
else:
    checks.append(("✗", "app.py MANQUANT"))
    sys.exit(1)

# 5. .gitignore existe
if os.path.exists(".gitignore"):
    checks.append(("✓", ".gitignore existe (secrets protégés)"))
else:
    checks.append(("⚠", ".gitignore manquant (créez-le!)"))

# Afficher les résultats
print("\n".join([f"{icon} {msg}" for icon, msg in checks]))

# Résumé
errors = sum(1 for icon, _ in checks if icon == "✗")
warnings = sum(1 for icon, _ in checks if icon == "⚠")

print("\n" + "="*50)
if errors == 0:
    print("✅ Configuration OK pour Vercel!")
    if warnings > 0:
        print(f"⚠️  {warnings} avertissement(s)")
else:
    print(f"❌ {errors} erreur(s) détectée(s)")
    sys.exit(1)

print("\n📚 Prochaines étapes:")
print("1. Générez ADMIN_PASSWORD fort")
print("2. Générez SECRET_KEY: python -c \"import secrets; print(secrets.token_hex(32))\"")
print("3. Poussez sur GitHub")
print("4. Importez sur https://vercel.com/new")
print("5. Configurez les variables d'environnement")
print("6. Déployez!")
