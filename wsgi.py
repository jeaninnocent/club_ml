"""
WSGI Configuration pour PythonAnywhere
À personnaliser avec vos variables d'environnement
"""
import os
import sys

# ============================================================
# ⚠️ À REMPLACER : Votre nom d'utilisateur PythonAnywhere
# ============================================================
USERNAME = "gnienlyomou"  # Ex: "johnsmith"

# Ajouter le chemin de l'app
sys.path.insert(0, f"/home/{USERNAME}/club")

# ============================================================
# Configuration des variables d'environnement
# ============================================================
os.environ["ADMIN_PASSWORD"] = "170MLDL@GENAI"  # ⚠️ À CHANGER par un mot de passe fort
os.environ["SECRET_KEY"] = "735c9dcf7dd5599a0ee17312abe4c87326bdb77e4ccf97bfc6bb2d312b59fea0"  # ⚠️ À GÉNÉRER
os.environ["DB_PATH"] = f"/home/{USERNAME}/club/club.db"

# ============================================================
# Import l'application Flask
# ============================================================
from app import app as application
