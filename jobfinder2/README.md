# JobFinder CI — Plateforme d'Emploi Django

Plateforme d'emploi complète pour la Côte d'Ivoire et l'Afrique.  
Django 5 · MySQL · IA Gratuite (Groq/Llama3) · Scraping réel

---

## ⚡ Installation rapide

```bash
# 1. Extraire et entrer dans le projet
unzip jobfinder_ci.zip
cd jobfinder_django

# 2. Environnement virtuel
python -m venv venv
source venv/bin/activate          # Mac/Linux
venv\Scripts\activate             # Windows

# 3. Dépendances
pip install -r requirements.txt

# 4. Configuration
cp .env.example .env
# → Éditer .env (DB MySQL + clé Groq)

# 5. Créer la DB dans phpMyAdmin
# → Nom: jobfinder_db, Interclassement: utf8mb4_unicode_ci

# 6. Migrations
python manage.py makemigrations accounts jobs employers applications ai_tools core
python manage.py migrate

# 7. Données de démo
python manage.py seed_data

# 8. Lancer
python manage.py runserver
```

Ouvrir : **http://127.0.0.1:8000**

---

## 🔑 Comptes de démo

| Rôle | Email | Mot de passe |
|---|---|---|
| Candidat | `demo@jobfinder.ci` | `Demo2025!` |
| Recruteur | `recruteur@cinettech.ci` | `Recruteur2025!` |
| Admin | `admin@jobfinder.ci` | `Admin2025!` |

---

## 🤖 IA Gratuite — Groq

1. Créez un compte sur **https://console.groq.com** (100% gratuit, pas de CB)
2. Créez une clé API
3. Ajoutez dans `.env` : `GROQ_API_KEY=gsk_...`
4. Redémarrez : `python manage.py runserver`

Modèles utilisés : `llama3-8b-8192` (rapide) et `llama3-70b-8192` (précis)

---

## 🔍 Scraping

```bash
# Scraper agenceemploijeunes.ci (réel)
python manage.py scrape_jobs --source aeji --pages 3

# Scraper LinkedIn CI
python manage.py scrape_jobs --source linkedin

# Tout scraper
python manage.py scrape_jobs --source all --pages 2

# Calculer les scores de matching
python manage.py compute_matches
```

---

## 📁 Structure

```
jobfinder_django/
├── jobfinder/          # Config (settings, urls, wsgi)
├── core/               # Accueil, Dashboard, templatetags
├── accounts/           # Utilisateurs, Profils, Auth par email
├── jobs/               # Offres, Matching, Sauvegarde, Scraper
│   └── management/commands/  seed_data, scrape_jobs, compute_matches
├── employers/          # Espace recruteur, Publication d'offres
├── applications/       # Candidatures, Suivi statuts
├── ai_tools/           # 6 outils IA (Groq/Llama3)
│   └── groq_client.py  # Client API Groq gratuit
├── templates/          # 15 templates HTML
├── static/css/         # Design system (Inter + Playfair Display)
├── .env.example
└── requirements.txt
```

---

## 🌐 Pages disponibles

| URL | Page |
|---|---|
| `/` | Accueil |
| `/auth/login/` | Connexion / Inscription |
| `/dashboard/` | Tableau de bord candidat |
| `/jobs/` | Liste des offres (filtres, pagination) |
| `/jobs/<id>/` | Détail d'une offre + Candidature IA |
| `/jobs/saved/` | Offres sauvegardées |
| `/applications/` | Historique candidatures |
| `/auth/profile/` | Profil (5 onglets) |
| `/employers/` | Espace recruteur |
| `/employers/post/` | Publier une offre |
| `/ai/` | 6 outils IA |
| `/admin/` | Interface administration |

---

## ⚙️ Variables d'environnement (.env)

```env
SECRET_KEY=votre-cle-secrete-longue
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MySQL (XAMPP par défaut)
DB_NAME=jobfinder_db
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306

# IA Gratuite Groq
GROQ_API_KEY=gsk_VOTRE_CLE
```

---

## 🐛 Problèmes fréquents

**`No module named 'MySQLdb'`**
```bash
pip install PyMySQL
# Dans jobfinder/__init__.py : import pymysql; pymysql.install_as_MySQLdb()
```

**`No such table`**
```bash
python manage.py makemigrations
python manage.py migrate
```

**Static files manquants**
```bash
mkdir static static\css static\js static\img
python manage.py collectstatic
```

---

Made with ♥ in 🇨🇮 Côte d'Ivoire
