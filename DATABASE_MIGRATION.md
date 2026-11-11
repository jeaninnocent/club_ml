# Migration SQLite → PostgreSQL

Guide pour migrer vers PostgreSQL une fois en production sur Vercel.

## Pourquoi migrer?

- ✓ Persistance garantie sur Vercel
- ✓ Meilleure performance en production
- ✓ Support de plusieurs instances/workers
- ✓ Backups et recovery intégrés

## Option 1: Supabase (Recommandée - Gratuit)

### Étape 1: Créer un projet Supabase

1. Allez sur [supabase.com](https://supabase.com)
2. Créez un compte gratuit
3. "New Project" → Remplissez les infos
4. Attendez la création (2-5 min)
5. Récupérez l'URL et la clé API

### Étape 2: Ajouter la dépendance

```bash
pip install psycopg2-binary SQLAlchemy flask-sqlalchemy
```

Mettez à jour `requirements.txt`:
```
flask>=3.0
werkzeug>=3.0
psycopg2-binary>=2.9
flask-sqlalchemy>=3.0
```

### Étape 3: Refactoriser app.py

Remplacez la BD SQLite par SQLAlchemy + PostgreSQL:

```python
# À AJOUTER au début de app.py
from flask_sqlalchemy import SQLAlchemy
import os

# Configuration PostgreSQL
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL or "sqlite:///club.db"
db = SQLAlchemy(app)

# Modèles
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    level = db.Column(db.String(50), default="")
    pw = db.Column(db.String(255), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    descr = db.Column(db.Text, default="")
    deadline = db.Column(db.String(10), default="")
    xp = db.Column(db.Integer, default=100)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    at = db.Column(db.String(30), nullable=False)
    note = db.Column(db.Float)
    comment = db.Column(db.Text, default="")
    xp_awarded = db.Column(db.Integer, default=0)
```

### Étape 4: Migrer les données

Script de migration SQLite → PostgreSQL:

```python
# migrate_db.py
import sqlite3
import psycopg2
import os
from datetime import datetime

# Connexions
sqlite_conn = sqlite3.connect("club.db")
sqlite_conn.row_factory = sqlite3.Row
postgres_url = os.environ["DATABASE_URL"]

postgres_conn = psycopg2.connect(postgres_url)

print("📊 Migration SQLite → PostgreSQL...")

# Migrer users
for user in sqlite_conn.execute("SELECT * FROM users"):
    postgres_conn.execute(
        "INSERT INTO users(id, username, name, level, pw) VALUES(%s, %s, %s, %s, %s)",
        (user["id"], user["username"], user["name"], user["level"], user["pw"])
    )
print(f"✓ {len(list(sqlite_conn.execute('SELECT * FROM users')))} apprenants migrés")

# Migrer tasks
for task in sqlite_conn.execute("SELECT * FROM tasks"):
    postgres_conn.execute(
        "INSERT INTO tasks(id, title, descr, deadline, xp) VALUES(%s, %s, %s, %s, %s)",
        (task["id"], task["title"], task["descr"], task["deadline"], task["xp"])
    )
print(f"✓ {len(list(sqlite_conn.execute('SELECT * FROM tasks')))} exercices migrés")

# Migrer submissions
for sub in sqlite_conn.execute("SELECT * FROM subs"):
    postgres_conn.execute(
        "INSERT INTO subs(id, user_id, task_id, url, at, note, comment, xp_awarded) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)",
        (sub["id"], sub["user_id"], sub["task_id"], sub["url"], sub["at"], sub["note"], sub["comment"], sub["xp_awarded"])
    )
print(f"✓ {len(list(sqlite_conn.execute('SELECT * FROM subs')))} rendus migrés")

postgres_conn.commit()
print("✅ Migration complète!")
```

### Étape 5: Configurer Vercel

1. Allez dans **Settings** → **Environment Variables**
2. Ajoutez `DATABASE_URL` = (URL de Supabase)

### Étape 6: Déployer

```bash
git add .
git commit -m "Migrate to PostgreSQL"
git push origin main
```

Vercel redéploiera automatiquement.

---

## Option 2: MongoDB Atlas (Alternative)

Plus simple mais moins SQL-ish:

1. Allez sur [mongodb.com/cloud/atlas](https://mongodb.com/cloud/atlas)
2. Créez un cluster gratuit
3. Utilisez `pymongo` pour accéder

---

## Option 3: Garder SQLite (Dev/Test seulement)

Si vous voulez juste tester sur Vercel sans BD:

- La BD est réinitialisée à chaque redéploiement
- Parfait pour faire des démos
- ❌ PAS recommandé pour production

---

## Rollback: Revenir à SQLite

Si vous avez un problème avec PostgreSQL:

```bash
git revert <commit>
git push origin main
```

Vercel redéploiera avec la version SQLite.

---

## Benchmarks

| Métrique | SQLite | PostgreSQL |
|----------|--------|------------|
| Persistance | ❌ Non | ✓ Oui |
| Latence requête | ~5ms | ~20ms |
| Concurrent users | 1-2 | 100+ |
| Backups | ❌ | ✓ Auto |
| Coût | Gratuit | Gratuit (50GB) |

Pour une vraie production: **PostgreSQL obligatoire**.

---

## Support

Besoin d'aide?
- Supabase docs: https://supabase.com/docs/guides/migrations/migrate-from-sqlite
- Flask-SQLAlchemy: https://flask-sqlalchemy.palletsprojects.com/
- Vercel + Python: https://vercel.com/docs/functions/serverless-functions/python
