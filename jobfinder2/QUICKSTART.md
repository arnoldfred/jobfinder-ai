# GUIDE DE DÉMARRAGE RAPIDE — JobFinder v2.1

## 🎯 Résumé des 3 Problèmes Résolus

| Problème | Solution | Fichier |
|----------|----------|---------|
| **Profil ne permet pas de modifier** | Bouton "Modifier" ajouté | `templates/accounts/profile.html` |
| **LinkedIn: Offres invalides/404/morts** | Validation HTTP + filtrage régional | `jobs/scraper.py` |
| **Pas les bonnes régions (pas Afrique)** | GeoID CI + keywords régionaux | `jobs/scraper.py` |

---

## ⚡ Démarrage en 5 Minutes

### 1️⃣ Vérifier la Page de Profil
```
→ Allez sur http://localhost:8000/auth/profile/
→ Vous verrez le bouton "Modifier" en haut à droite ✓
```

### 2️⃣ Tester le Scraper LinkedIn Amélioré
```bash
cd jobfinder2
python scrape_now.py
```
✓ Vous verrez les logs des offres filtrées  
✓ Seulement les offres Côte d'Ivoire (pas USA/Europe)  
✓ Liens vérifiés valides

### 3️⃣ Nettoyer les Vieux Liens
```bash
# Vérifier d'abord
python check_and_clean_dead_links.py --dry-run

# Puis appliquer
python check_and_clean_dead_links.py
```
✓ Marque les liens 404 comme inactifs

### 4️⃣ Maintenance Complète (Recommandé)
```bash
# Une seule commande pour tout:
python maintenance_complete.py
```
✓ Scrape LinkedIn  
✓ Filtre par région  
✓ Nettoie les liens  
✓ Génère un rapport

---

## 📱 Exemple: Page de Profil

**Avant:**
- Onglets seulement
- Pas de bouton visible "Modifier"
- Utilisateur doit cliquer sur "Infos" tab

**Après:**
- ✅ Bouton "Modifier" en haut à droite
- ✅ Clique → va directement au tab "Infos"
- ✅ Interface plus intuitive

```html
<!-- Nouveau bouton -->
<a href="?tab=personal" class="btn btn-primary">
  <i data-lucide="edit-3"></i> Modifier
</a>
```

---

## 🌍 Exemple: Filtrage LinkedIn

**Avant:**
```
❌ Offre à New York, USA
❌ Offre à Paris, France  
❌ Offre à Singapour
❌ Lien retourne 404
```

**Après:**
```
✅ Offre à Abidjan, CI
✅ Offre à Accra, Ghana
✅ Offre "Afrique Ouest"
✅ Lien vérifié HTTP 200
```

**Filtrage appliqué:**
- Accepte: 81+ villes africaines + régions
- Rejette: USA, Europe, Asie
- Valide: Chaque lien avec HEAD request

---

## 🔄 Automatisation (Optionnel)

### Pour Windows (Task Scheduler):

1. Créez un fichier `run_maintenance.bat`:
```batch
@echo off
cd E:\jobfinder_ai_v2.1\jobfinder2
python maintenance_complete.py >> logs\maintenance.log 2>&1
```

2. Ouvrez Task Scheduler (WIN+R → taskschd.msc)
3. Actions → Create Basic Task
4. Nom: "JobFinder Maintenance"
5. Triggers: Quotidienne à 6h
6. Actions: Exécuter `run_maintenance.bat`

### Pour Linux/Mac (Crontab):
```bash
crontab -e
# Ajouter:
0 6 * * * cd /path/to/jobfinder2 && python maintenance_complete.py >> logs/maintenance.log 2>&1
```

---

## 📊 Monitoring (Vérifier que tout fonctionne)

### Vérifier les offres en base:
```bash
python manage.py shell
>>> from jobs.models import Job
>>> Job.objects.filter(is_active=True, country='CI').count()
```

### Voir le dernier sync LinkedIn:
```bash
>>> from jobs.models import JobSource
>>> source = JobSource.objects.get(name='LinkedIn Jobs CI')
>>> print(f"Offres: {source.jobs_scraped}, Dernier sync: {source.last_sync}")
```

### Vérifier les liens morts:
```bash
python check_and_clean_dead_links.py --dry-run
# Affichera les offres avec liens 404/timeout
```

---

## 🐛 Troubleshooting Rapide

### Q: "Aucune offre trouvée"
```bash
# DEBUG:
from jobs.scraper import scrape_linkedin_ci
import logging
logging.basicConfig(level=logging.DEBUG)
result = scrape_linkedin_ci()
print(f"Offres trouvées: {len(result)}")
```

### Q: "Toutes les offres sont filtrées"
```bash
# Vérifier le filtrage:
python manage.py filter_jobs_by_region --dry-run
# Ajustez les villes dans filter_jobs_by_region.py si besoin
```

### Q: "Liens toujours 404"
- Normal pour LinkedIn (liens temporaires de 24-48h)
- Exécutez `check_and_clean_dead_links.py` régulièrement
- C'est pourquoi `maintenance_complete.py` le fait auto

### Q: "Veut utiliser compte LinkedIn?"
- ✓ Optionnel, pas nécessaire
- Voir `GITHUB_LINKEDIN_CONFIG.md` si vous voulez

---

## 📁 Structure des Fichiers

```
jobfinder2/
├── check_and_clean_dead_links.py     ← Nettoyage liens
├── maintenance_complete.py             ← All-in-one
├── CHANGEMENTSUMÉ.md                   ← Documentation complète
├── GITHUB_LINKEDIN_CONFIG.md           ← Config LinkedIn
├── templates/accounts/profile.html     ← Bouton "Modifier"
├── jobs/
│   ├── scraper.py                     ← Scraper amélioré
│   └── management/commands/
│       └── filter_jobs_by_region.py   ← Filtrage régional
└── logs/                              ← Logs auto-créés
```

---

## 🎓 Cas d'Usage Courant

### Matin (Test rapide):
```bash
python scrape_now.py
# → ~2 min, ~20-30 offres
```

### Hebdomadaire (Nettoyage):
```bash
python maintenance_complete.py
# → ~5 min, nettoie tout, rapport détaillé
```

### Mensuel (Archivage):
```bash
python maintenance_complete.py --clean-old 30
# → Supprime les offres inactives depuis > 30j
```

---

## ✅ Vérification Continue

**Activer les logs:**
```python
# jobs/settings.py (ajouter):
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/scraper.log',
        },
    },
    'loggers': {
        'jobs.scraper': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

Puis vérifiez les logs:
```bash
tail -f logs/scraper.log
```

---

## 🚀 Prochaines Étapes

### Immédiat:
1. ✅ Tester la page de profil (bouton "Modifier")
2. ✅ Exécuter `python maintenance_complete.py` une fois
3. ✅ Vérifier les offres en base de données

### Court terme:
- Automatiser avec task scheduler/cron
- Monitorer régulièrement les logs
- Ajuster les villes/régions si besoin

### Futur:
- Ajouter d'autres sources (BeeJob, TalentCI, etc)
- Dashboard analytics des offres
- Alertes par email

---

## 💡 Conseil d'Or

**N'exécutez pas:**
- `python scrape_now.py` plus de 2-3× par jour (rate limit LinkedIn)
- `check_and_clean_dead_links` sur 10000+ offres (prend du temps)

**À la place:**
- Utilisez `maintenance_complete.py` une fois par jour
- Elle gère les delays et timeouts automatiquement
- Elle génère des rapports résumés

---

## 📚 Ressources

| Besoin | Où regarder |
|--------|------------|
| Configuration complète | `GITHUB_LINKEDIN_CONFIG.md` |
| Liste des changements | `CHANGEMENTS_RESUME.md` |
| Scraping LinkedIn | `jobs/scraper.py#L287` |
| Filtrage régional | `jobs/management/commands/filter_jobs_by_region.py` |
| Nettoyage liens | `check_and_clean_dead_links.py` |

---

**Vous êtes prêt! 🎉**

Lancez: `python maintenance_complete.py` et voyez la magie opérer!

*Support: Voir GITHUB_LINKEDIN_CONFIG.md ou commentaires dans le code*
