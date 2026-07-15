#!/usr/bin/env python
"""
Autoscrap script pour les offres d'emploi
Usage: python scrape_automatically.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
sys.path.insert(0, os.path.dirname(__file__))

# Initialiser Django AVANT d'importer les modèles
django.setup()

from jobs.scraper import scrape_agenceemploijeunes, scrape_linkedin_ci
from datetime import datetime

def main():
    print(f"🚀 Scraping started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # AEJI Scraping
    print("\n💼 Scraping agenceemploijeunes.ci...")
    try:
        aeji_jobs = scrape_agenceemploijeunes(max_pages=2)
        print(f"✅ {len(aeji_jobs)} offres AEJI ajoutées")
    except Exception as e:
        print(f"❌ Erreur AEJI: {e}")
        aeji_jobs = []
    
    # LinkedIn Scraping
    print("\n💼 Scraping LinkedIn CI...")
    try:
        linkedin_jobs = scrape_linkedin_ci(max_results=20)
        print(f"✅ {len(linkedin_jobs)} offres LinkedIn ajoutées")
    except Exception as e:
        print(f"❌ Erreur LinkedIn: {e}")
        linkedin_jobs = []
    
    total = len(aeji_jobs) + len(linkedin_jobs)
    print(f"\n✅ Au total: {total} nouvelles offres scrapées!")
    print(f"📌 Les offres sont disponibles sur /jobs/")
    print(f"⏰ Scraping terminé à {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

if __name__ == '__main__':
    main()
