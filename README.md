# 🎓 Plateforme du Club Machine Learning

Plateforme complète de gestion d'exercices et de notation pour un club d'apprentissage en Machine Learning.

**🚀 Déploiement recommandé:** [Vercel](#déploiement-vercel) (gratuit, serverless, ultra-rapide)

## 🎯 Fonctionnalités

### 👥 Espace Apprenant
- 📚 Voir les exercices publiés
- 📤 Soumettre des rendus (repos GitHub)
- 📊 Consulter son XP et ses notes
- 🏆 Voir le classement global
- 💬 Lire les commentaires de l'admin

### 🔐 Espace Admin
- 👤 Créer et gérer les comptes apprenants
- 📝 Publier des exercices avec deadlines
- 📋 Noter les rendus et ajouter des commentaires
- 📊 Dashboard avec statistiques
- 🔑 Générer des mots de passe temporaires

## 🚀 Lancer en local

### Installation
```bash
pip install -r requirements.txt
```

### Windows (CMD)
```cmd
set ADMIN_PASSWORD=170MLDL@GENAI && python app.py
```

### Windows (PowerShell)
```powershell
$env:ADMIN_PASSWORD="170MLDL@GENAI"; python app.py
```

### macOS / Linux
```bash
ADMIN_PASSWORD="170MLDL@GENAI" python app.py
```

Ouvrez :
- **Apprenants** : http://localhost:5000/login
- **Admin** : http://localhost:5000/admin/login (user: `admin`, password: `170MLDL@GENAI`)

---

## ☁️ Déploiement sur Vercel (Recommandé ✨)

**Avantages:** Gratuit, serverless, déploiement en 5 min, automatique sur push Git

### 🚀 Guide Rapide (5 minutes)

Voir **`VERCEL_QUICK_START.txt`** pour les étapes détaillées.

### 📋 Étapes Essentielles

1. **Générer les credentials sécurisés:**
   ```bash
   python generate_credentials.py
   ```

2. **Pousser sur GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/VOTRE_USERNAME/club-ml-plateforme.git
   git push -u origin main
   ```

3. **Importer sur Vercel:**
   - Allez sur https://vercel.com/new
   - Connectez-vous avec GitHub
   - Sélectionnez votre repo
   - Cliquez "Import"

4. **Configurer les variables d'environnement:**
   - Settings → Environment Variables
   - Ajoutez: `ADMIN_USER`, `ADMIN_PASSWORD`, `SECRET_KEY`, `DB_PATH`

5. **Déployer:**
   - Cliquez "Deploy"
   - Attendez 2-3 minutes
   - ✓ C'est fait!

### 📚 Documentation Complète
- `VERCEL_QUICK_START.txt` - Guide rapide
- `VERCEL_DEPLOYMENT.md` - Documentation détaillée
- `DEPLOYMENT_CHECKLIST.md` - Checklist étape par étape
- `DATABASE_MIGRATION.md` - Migrer vers PostgreSQL (production)

---

## ☁️ Déploiement sur PythonAnywhere (Alternative)

### 📖 Guide Complet
Voir le fichier **`DEPLOYMENT_GUIDE.md`** pour des instructions détaillées étape par étape.

### ⚡ Guide Rapide
Voir le fichier **`QUICK_START_PYTHONANYWHERE.txt`** pour un résumé rapide.

### 📋 Fichiers Nécessaires
- `app.py` - Application principale
- `requirements.txt` - Dépendances Python
- `wsgi.py` - Configuration WSGI (à personnaliser avec votre username)
- `club.db` - Base de données (créée automatiquement si absente)

### 🔧 Étapes Rapides
1. Créez un compte sur [pythonanywhere.com](https://www.pythonanywhere.com)
2. Téléchargez les fichiers dans un dossier `club`
3. Installez Flask : `pip install --user flask`
4. Créez une web app manuel Python 3.10+
5. Configurez le fichier WSGI avec vos paramètres
6. Générez une clé secrète sécurisée
7. Rechargez l'app
8. Forcez HTTPS

---

## 📖 Utilisation

### 👤 Admin - Gestion des Apprenants
1. Allez dans **👥 Gestion des apprenants**
2. Entrez les noms (format : `Nom Complet; Niveau`)
3. Les identifiants et mots de passe sont générés automatiquement
4. Imprimez ou notez les identifiants à transmettre

**Exemple :**
```
Awa Koné; L3
Jean Kouassi; L2
Marie Dupont
```

### 📝 Admin - Créer un Exercice
1. Allez dans **✨ Tableau de bord**
2. Remplissez : titre, consignes, deadline (optionnel), XP max
3. Cliquez sur **✓ Publier l'exercice**

Les XP attribués = (XP max × note apprenant) / 20

### ⭐ Admin - Noter les Rendus
1. Cliquez sur **Rendus & notes** d'un exercice
2. Consultez les rendus GitHub
3. Entrez une note (/20) et un commentaire optionnel
4. Les XP sont calculés automatiquement

### 🎓 Apprenant - Soumettre un Rendu
1. Cliquez sur un exercice
2. Entrez le lien vers votre repo GitHub
3. Le rendu est enregistré
4. Mettez à jour jusqu'à la deadline

### 🏆 Classement
- Affiche le top 10 en vert
- Reste en orange
- Les 3 premiers ont des badges spéciaux
- Visible par tous les apprenants

---

## 🔐 Sécurité

- ✅ Mots de passe hashés (werkzeug)
- ✅ CSRF protection sur tous les formulaires
- ✅ Rate limiting (8 tentatives = throttle 5 min)
- ✅ Sessions sécurisées (HttpOnly, SameSite)
- ✅ HTTPS recommandé en production

---

## 💾 Sauvegarde & Maintenance

**Base de données :** Tous les données sont dans `club.db`
- Copiez-le régulièrement pour sauvegarder
- À l'abri, vous pouvez réinstancier l'app sans perte

**Sur PythonAnywhere :**
1. Allez dans **Files → club**
2. Téléchargez régulièrement `club.db`

---

## 🎨 Design

- ✨ Interface moderne et responsive
- 🌙 Dark mode automatique
- 🎯 UX optimisée pour admin et apprenants
- 📱 Mobile-friendly

---

## 📞 Support

### Erreurs Courantes

**"ADMIN_PASSWORD n'est pas configuré"**
→ Assurez-vous de définir la variable d'environnement

**"Permission denied" sur club.db**
→ Vérifiez les permissions du fichier sur le serveur

**Page blanche (erreur 500)**
→ Consultez les logs d'erreur dans PythonAnywhere

---

## 📦 Dépendances

- Flask >= 3.0
- Werkzeug (inclus avec Flask)
- Python 3.10+

---

## 📄 Licence & Attribution

Plateforme développée pour clubs de Machine Learning.
Libre d'utilisation et de modification.

---

**Besoin d'aide ?** Consultez les guides détaillés :
- 📖 `DEPLOYMENT_GUIDE.md` - Guide complet PythonAnywhere
- ⚡ `QUICK_START_PYTHONANYWHERE.txt` - Résumé rapide
- 🔐 `generate_secret.py` - Générer une clé secrète sécurisée
