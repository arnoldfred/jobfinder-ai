# 🤖 SCRAPING AUTOMATIQUE - GUIDE D'INSTALLATION

Le scraping des offres d'emploi est maintenant automatisé! Voici comment le configurer.

## Option 1: Windows Task Scheduler (Recommandé) ⭐

### Étapes:

1. **Ouvrir Task Scheduler**
   - Appuyer sur `Win + R`
   - Taper: `taskschd.msc`
   - Appuyer sur `Enter`

2. **Créer une tâche planifiée**
   - Clic droit → "Create Task"
   - Remplir:
     - Name: `JobFinder-Scraper`
     - Description: `Scrape jobs from AEJI and LinkedIn daily`
     - Cocher: "Run with highest privileges"

3. **Onglet "Triggers"**
   - Clic sur "New"
   - Choisir: "Daily" ou "On a schedule"
   - Heure recommandée: **02:00 AM** (heures creuses)
   - Cocher: "Enabled"

4. **Onglet "Actions"**
   - Clic sur "New"
   - Action type: "Start a program"
   - Program: `e:\jobfinder_ai_v2.1\jobfinder2\run_scraper.bat`
   - Appuyer sur OK

5. **Onglet "Conditions"**
   - Décocher "Stop the task if it runs longer than"

6. **Clic OK pour créer la tâche**

### Vérifier que ça marche:
```
Clic droit sur la tâche → "Run" pour l'exécuter maintenant
```

---

## Option 2: PowerShell Scheduling

```powershell
# Créer une tâche planifiée via PowerShell

$action = New-ScheduledTaskAction -Execute 'e:\jobfinder_ai_v2.1\.venv\Scripts\python.exe' -Argument 'e:\jobfinder_ai_v2.1\jobfinder2\scrape_automatically.py' -WorkingDirectory 'e:\jobfinder_ai_v2.1\jobfinder2'

$trigger = New-ScheduledTaskTrigger -Daily -At 2am

Register-ScheduledTask -Action $action -Trigger $trigger -TaskName 'JobFinder-Scraper' -Description 'Automatic scraping of job offers'
```

---

## Option 3: Exécution Manuelle

Double-cliquer sur: `run_scraper.bat`

```
OU en terminal:
e:\jobfinder_ai_v2.1\jobfinder2> python scrape_automatically.py
```

---

## 📊 Vérifier les Logs

Les logs sont sauvegardés dans: `scraping_log.txt`

```bash
Type scraping_log.txt
```

---

## 🔄 Fréquence Recommandée

- **Daily**: Une fois par jour (02:00 AM)
- **Timezone**: En heure locale
- **Rétention logs**: Garder 30 derniers jours

---

## ✅ Status de Scraping

- **AEJI**: `agenceemploijeunes.ci/site` (2 pages)
- **LinkedIn**: LinkedIn Jobs CI (20 offres max)
- **Résultat**: Offres dupliquées ignorées automatiquement

---

## 🆘 Troubleshooting

**Problème**: La tâche ne s'exécute pas
- ✓ Vérifier que le chemin du script est correct
- ✓ Vérifier que le venv existe: `.venv/Scripts/python.exe`
- ✓ Relancer Task Scheduler

**Problème**: 0 offres scrapées
- ✓ C'est normal si les sites limite l'accès
- ✓ Les offres précédentes restent dans la BD
- ✓ Vérifier: `scraping_log.txt`

---

## 📝 Notes

- Les offres scrapées sont ajoutées à la base de données MySQL
- Les doublons sont détectés et ignorés
- Les offres du site AEJI ont des détails complets (lieu, diplôme, contrat, etc.)
- Les offres LinkedIn ont un lien direct vers l'offre

---

**Script créé**: `scrape_automatically.py`
**Batch file créé**: `run_scraper.bat`
**Configuration**: `scrape_jobs` management command
