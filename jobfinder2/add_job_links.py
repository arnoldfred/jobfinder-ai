#!/usr/bin/env python
"""Ajoute les liens externes aux offres (pour le bouton Postuler)"""
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobfinder.settings")
django.setup()

from jobs.models import Job

# Ajouter les liens aux offres AEJI
aeji_jobs = [
    ('Stagiaire Comptable', 'https://agenceemploijeunes.ci/site/offres?search=comptable'),
    ('Développeur Web Junior', 'https://agenceemploijeunes.ci/site/offres?search=developpeur'),
    ('Chargée Communication Digitale', 'https://agenceemploijeunes.ci/site/offres?search=communication'),
    ('Responsable RH', 'https://agenceemploijeunes.ci/site/offres?search=rh'),
    ('Assistant Comptable', 'https://agenceemploijeunes.ci/site/offres?search=comptable'),
]

print("📎 Ajout des liens de postulation...\n")

for title, url in aeji_jobs:
    job = Job.objects.filter(title=title, scraping_source__name='Agence Emploi Jeunes CI').first()
    if job:
        job.external_url = url
        job.save(update_fields=['external_url'])
        print(f"✅ {title}")
        print(f"   🔗 {url}\n")

# Ajouter les liens aux offres test (formulaire interne)
test_jobs = [
    ('Développeur Python Django', 'http://127.0.0.1:8000/jobs/apply/'),
    ('Data Analyst / Reporting', 'http://127.0.0.1:8000/jobs/apply/'),
    ('Développeur Frontend React.js', 'http://127.0.0.1:8000/jobs/apply/'),
    ('Responsable Comptabilité', 'http://127.0.0.1:8000/jobs/apply/'),
    ('Chef de Projet Digital', 'http://127.0.0.1:8000/jobs/apply/'),
]

for title, url in test_jobs:
    job = Job.objects.filter(title=title, scraping_source__name='Données Manuelles/Test').first()
    if job:
        job.external_url = url
        job.save(update_fields=['external_url'])
        print(f"✅ {title}")
        print(f"   🔗 {url}\n")

print("✨ Tous les liens ajoutés!")
