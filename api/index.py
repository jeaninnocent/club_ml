"""
Configuration Vercel Serverless pour Club ML Plateforme
"""
import sys
import os

# Ajouter le parent directory au path pour importer app.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# ============================================================
# Pour Vercel, l'app Flask est exportée comme `app`
# ============================================================
