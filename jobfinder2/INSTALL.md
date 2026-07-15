# JobFinder AI — Guide d'installation

## ⚠️ Problème fréquent : `No module named 'distutils'`

**Cause** : Python 3.12 a supprimé le module `distutils`. Django 3.2 en a besoin.

**Solution en 1 commande :**
```bash
pip install setuptools
```

Puis relancez normalement.

---

## Installation complète (Windows XAMPP)

### 1. Prérequis
- Python 3.10 ou 3.11 (recommandé) ou 3.12 avec fix ci-dessus
- XAMPP avec MySQL démarré
- La base de données `jobfinder_db` créée dans phpMyAdmin

### 2. Créer la base de données
Dans phpMyAdmin → Nouvelle base de données :
```sql
CREATE DATABASE jobfinder_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Installer les dépendances

**Option A — Script automatique (Windows) :**
```
double-cliquer sur start.bat
```

**Option B — Manuel :**
```bash
# Dans le dossier jobfinder2/
pip install setuptools          # ← TOUJOURS EN PREMIER sur Python 3.12
pip install -r requirements.txt
```

### 4. Configuration (.env)
Le fichier `.env` est déjà configuré pour XAMPP. Vérifiez :
```
DB_NAME=jobfinder_db
DB_USER=root
DB_PASSWORD=          # vide pour XAMPP
DB_HOST=127.0.0.1
DB_PORT=3306
GROQ_API_KEY=gsk_...  # votre clé API Groq (console.groq.com)
```

### 5. Migrations et données
```bash
python manage.py migrate
python manage.py seed_data        # offres de démonstration
python manage.py createsuperuser  # compte administrateur
```

### 6. Lancer
```bash
python manage.py runserver
```
→ http://127.0.0.1:8000

---

## Scraping des offres
```bash
python manage.py scrape_jobs --source all --pages 3 --match
```

## Comptes de test (après seed_data)
| Rôle | Email | Mot de passe |
|------|-------|--------------|
| Candidat | demo@jobfinder.ai | Demo2025! |
| Recruteur | recruteur@cinettech.ci | Recruteur2025! |
| Admin | Créez-le avec `createsuperuser` | — |

---

## Erreurs fréquentes

### `No module named 'distutils'`
```bash
pip install setuptools
```

### `django.db.utils.OperationalError: (2003, "Can't connect to MySQL")`
→ Vérifiez que XAMPP MySQL est démarré et que `jobfinder_db` existe.

### `ModuleNotFoundError: No module named 'pymysql'`
```bash
pip install PyMySQL==1.1.1
```

### `ModuleNotFoundError: No module named 'sklearn'`
```bash
pip install scikit-learn==1.4.2
```
