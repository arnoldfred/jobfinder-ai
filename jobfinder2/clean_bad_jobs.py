#!/usr/bin/env python
"""
Nettoie les offres d'emploi mal scrappées (descriptions vides, skills manquants).
"""
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobfinder.settings")
django.setup()

from jobs.models import Job

# Supprimer les offres LinkedIn avec description générique/vide
bad_count = 0
for job in Job.objects.filter(scraping_source__name='LinkedIn Jobs CI'):
    # LinkedIn offres mal scrapées
    if not job.required_skills or job.required_skills.strip() == '':
        print(f"[DEL] {job.title} (pas de skills)")
        job.delete()
        bad_count += 1
    elif 'Cliquez sur' in job.description or len(job.description) < 50:
        print(f"[DEL] {job.title} (description vide)")
        job.delete()
        bad_count += 1

# Supprimer les offres AEJI avec description trop courte
for job in Job.objects.filter(scraping_source__name='Agence Emploi Jeunes CI'):
    if not job.required_skills or job.required_skills.strip() == '':
        print(f"[DEL] {job.title} (AEJI pas de skills)")
        job.delete()
        bad_count += 1

print(f"\n✓ {bad_count} offres mal scrappées supprimées")
print("Maintenant, réexécutez: python scrape_now.py")
