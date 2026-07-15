#!/usr/bin/env python
"""Script de scraping AEJI"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
django.setup()

from jobs.scraper import scrape_agenceemploijeunes

print("🚀 Début du scraping AEJI...\n")

try:
    jobs = scrape_agenceemploijeunes(max_pages=2)
    print(f'\n✅ {len(jobs)} offres scrapées avec succès!\n')
    
    for job in jobs[:10]:
        print(f"  • {job.title}")
        print(f"    URL: {job.external_url}")
        print(f"    Lieu: {job.location}\n")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
