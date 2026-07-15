#!/usr/bin/env python
"""Corriger les URLs LinkedIn et rescraper"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
django.setup()

from jobs.models import Job
from jobs.scraper import scrape_linkedin_ci

# Supprimer les offres LinkedIn cassées
Job.objects.filter(scraping_source__name='LinkedIn Jobs CI').delete()
print('✓ Anciennes offres LinkedIn supprimées')

# Rescraper
jobs = scrape_linkedin_ci(keyword='emploi Côte d\'Ivoire', max_results=30)
print(f'✓ {len(jobs)} nouvelles offres LinkedIn scrapées avec URLs corrigées!')

# Afficher les premières
print('\nVérification des URLs :')
print('=' * 70)
for job in Job.objects.filter(scraping_source__name='LinkedIn Jobs CI')[:5]:
    print(f'Titre: {job.title[:50]}')
    print(f'URL  : {job.external_url}')
    print('-' * 70)

print(f'\n✅ Total: {Job.objects.filter(scraping_source__name="LinkedIn Jobs CI").count()} offres LinkedIn actives')
