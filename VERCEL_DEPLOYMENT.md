# Déploiement sur Vercel

Guide complet pour déployer la plateforme Club ML sur Vercel.

## Prérequis

- Un compte GitHub avec le repo poussé
- Un compte [Vercel](https://vercel.com) (gratuit)
- Vercel CLI installé (optionnel mais recommandé)

## Étape 1: Préparer le dépôt Git

```bash
git init
git add .
git commit -m "Initial commit for Vercel deployment"
git remote add origin https://github.com/VOTRE_USERNAME/club-ml-plateforme.git
git push -u origin main
```

## Étape 2: Se connecter à Vercel

### Option A: Via le site Vercel (recommandé pour les débutants)

1. Allez sur [https://vercel.com/new](https://vercel.com/new)
2. Connectez-vous avec GitHub
3. Sélectionnez votre repo `club-ml-plateforme`
4. Cliquez sur "Import"

### Option B: Via Vercel CLI

```bash
npm i -g vercel
vercel
```

## Étape 3: Configurer les variables d'environnement

Après avoir importé le projet sur Vercel:

1. Allez dans votre projet Vercel → **Settings** → **Environment Variables**
2. Ajoutez les variables suivantes:

| Variable | Valeur | Description |
|----------|--------|-------------|
| `ADMIN_USER` | `admin` | Identifiant admin (à changer en production) |
| `ADMIN_PASSWORD` | `VOTRE_MOT_DE_PASSE_FORT` | ⚠️ **À générer et garder secret** |
| `SECRET_KEY` | `VOTRE_CLÉ_SECRÈTE` | Générez avec Python: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DB_PATH` | `/tmp/club.db` | Chemin de la BD (préset, ne pas modifier) |

**⚠️ IMPORTANT: Générez une nouvelle SECRET_KEY et ADMIN_PASSWORD!**

### Générer une clé secrète sécurisée

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Ou utilisez le script fourni:
```bash
python generate_secret.py
```

## Étape 4: Déployer

### Via site Vercel
- Cliquez sur "Deploy"
- Attendez que le déploiement se termine (2-3 minutes)

### Via CLI
```bash
vercel --prod
```

## Étape 5: Vérifier le déploiement

1. Votre app est maintenant à `https://votre-projet.vercel.app`
2. Testez:
   - Accès apprenant: `/login`
   - Accès admin: `/admin/login`

## ⚠️ Limitations sur Vercel (plan gratuit)

### Système de fichiers
- **Pas de persistance**: Les fichiers ne survivent pas au redémarrage
- **Workaround**: La BD est recréée à chaque déploiement/redémarrage
- **Solution à long terme**: Utiliser PostgreSQL (ex: ElephantSQL, Supabase)

### Performance
- Première requête plus lente (cold start)
- Les serveur "spin down" après 15 min d'inactivité

### Pour une BD persistante (recommandé):

**Option 1: Supabase (PostgreSQL gratuit)**
```python
import psycopg2
# À implémenter dans app.py
```

**Option 2: MongoDB Atlas (gratuit)**
```python
import pymongo
# À implémenter dans app.py
```

## Mise à jour du code

Chaque push sur `main` déclenche un redéploiement automatique:

```bash
git add .
git commit -m "Updates"
git push origin main
```

## Dépannage

### Erreur: "Python error: SQLite database is locked"
- Vercel n'a pas de système de fichiers persistant
- **Solution**: Implémenter une vraie BD (PostgreSQL/MongoDB)

### Erreur: "Module not found"
- Vérifiez que `requirements.txt` a toutes les dépendances
- Re-déployez après modification

### Erreur: "502 Bad Gateway"
- Vérifiez les logs Vercel: `vercel logs`
- Vérifiez les variables d'environnement

## Configuration avancée

### Domaine personnalisé

1. Allez dans **Settings** → **Domains**
2. Ajoutez votre domaine
3. Suivez les instructions DNS

### CORS

Modifier `app.py` si vous avez besoin d'un frontend séparé:

```python
from flask_cors import CORS
CORS(app)
```

### Fichiers statiques

Placez les CSS/JS dans `public/` et Vercel les servira automatiquement.

## Prochaines étapes

1. **Remplacer SQLite** par PostgreSQL pour une vraie persistance
2. **Ajouter HTTPS** (Vercel le fait automatiquement)
3. **Configurer un CDN** pour les assets
4. **Mettre en place des logs** (Vercel Logs)

---

**Questions?** Consultez:
- [Vercel Python Docs](https://vercel.com/docs/functions/quickstart/python)
- [Flask Deployment](https://flask.palletsprojects.com/deployment/)
