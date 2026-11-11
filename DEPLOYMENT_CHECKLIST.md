# ✅ Checklist Déploiement Vercel

Suivez cette checklist pour déployer sur Vercel sans oublier rien.

## Phase 1: Préparation locale

- [ ] Générer une nouvelle `SECRET_KEY`:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

- [ ] Générer un nouveau `ADMIN_PASSWORD` (fort, 16+ caractères):
  - Contient: majuscules, minuscules, chiffres, symboles
  - Ex: `P@ssw0rd!2024#Secure`

- [ ] Tester localement:
  ```bash
  python -m flask run
  ```
  - ✓ Accueil: http://localhost:5000
  - ✓ Login: http://localhost:5000/login
  - ✓ Admin: http://localhost:5000/admin/login

- [ ] Valider la structure Vercel:
  ```bash
  python test_vercel.py
  ```
  - Doit afficher: ✅ Configuration OK pour Vercel!

## Phase 2: Git & GitHub

- [ ] Initialiser le repo Git:
  ```bash
  git init
  git add .
  git commit -m "Initial commit for Vercel deployment"
  ```

- [ ] Créer un repo GitHub (https://github.com/new)

- [ ] Ajouter le remote:
  ```bash
  git remote add origin https://github.com/VOTRE_USERNAME/club-ml-plateforme.git
  git branch -M main
  git push -u origin main
  ```

- [ ] Vérifier sur GitHub que c'est poussé ✓

## Phase 3: Vercel

- [ ] Créer un compte Vercel: https://vercel.com/signup

- [ ] Importer le projet:
  - Allez sur https://vercel.com/new
  - Connectez-vous avec GitHub
  - Sélectionnez `club-ml-plateforme`
  - Cliquez "Import"

- [ ] Configurer les variables d'environnement:
  - Settings → Environment Variables
  - Ajouter:
    - `ADMIN_USER` = `admin`
    - `ADMIN_PASSWORD` = (votre mot de passe fort) ⚠️
    - `SECRET_KEY` = (votre clé générée) ⚠️
    - `DB_PATH` = `/tmp/club.db`

- [ ] Déployer:
  - Cliquez "Deploy"
  - Attendez 2-3 minutes
  - Vérifiez que le statut = ✓ Deployment successful

## Phase 4: Test en production

- [ ] Accéder à votre app:
  - URL: https://votre-projet.vercel.app (visible dans Vercel)

- [ ] Tester l'accès apprenant:
  - [ ] Aller à `/login`
  - [ ] Identifiant: `admin` (créé par défaut)
  - [ ] Mot de passe: (celui configuré)
  - [ ] Devrait fonctionner ✓

- [ ] Tester l'accès admin:
  - [ ] Aller à `/admin/login`
  - [ ] Identifiant: `admin`
  - [ ] Mot de passe: (celui configuré)
  - [ ] Devrait fonctionner ✓

- [ ] Vérifier les logs Vercel:
  - Dashboard → votre projet → Deployments → View Details
  - Doit afficher: ✓ Build & Deployments successful

## Phase 5: Documentation

- [ ] Partager l'URL avec l'équipe
- [ ] Documenter le mot de passe admin (stockage sécurisé, pas en clair!)
- [ ] Lire: `VERCEL_DEPLOYMENT.md` pour info complète
- [ ] Lire: `DATABASE_MIGRATION.md` pour la BD en production

## ⚠️ Sécurité - À faire ABSOLUMENT

- [ ] Ne JAMAIS committer `.secret`
- [ ] Ne JAMAIS committer `club.db`
- [ ] Ne JAMAIS committer de mot de passe en dur
- [ ] Utiliser les variables d'environnement Vercel (✓ ne sont pas dans le code)
- [ ] Vérifier `.gitignore` contient les fichiers sensibles

## 🔄 Mise à jour du code

Pour les futures mises à jour:

```bash
# Faire vos modifications
git add .
git commit -m "Description des changements"
git push origin main
# Vercel redéploiera automatiquement en 2-3 min
```

## 📞 Dépannage rapide

| Problème | Solution |
|----------|----------|
| `502 Bad Gateway` | Vérifiez les logs Vercel, rechargez |
| `Database locked` | C'est normal sur Vercel (SQLite limité) |
| `Module not found` | Re-déployez après modifier `requirements.txt` |
| `Environment variable error` | Vérifiez Settings → Environment Variables |

## ✅ Checklist finale

- [ ] App accessible à `https://votre-projet.vercel.app` ✓
- [ ] Login apprenant fonctionne ✓
- [ ] Login admin fonctionne ✓
- [ ] Code versionné sur GitHub ✓
- [ ] Variables d'environnement configurées ✓
- [ ] Pas de secrets en dur dans le code ✓

---

**✅ Félicitations! Votre plateforme est déployée sur Vercel!**

Prochaines étapes facultatives:
- [ ] Configurer un domaine personnalisé
- [ ] Migrer vers PostgreSQL (pour production)
- [ ] Mettre en place des backups
- [ ] Configurer les logs

Pour la migration PostgreSQL: consultez `DATABASE_MIGRATION.md`
