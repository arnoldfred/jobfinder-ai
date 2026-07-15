#!/usr/bin/env python
"""
Script pour scraper LinkedIn et AEJI et remplir la base
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
django.setup()

from jobs.scraper import scrape_agenceemploijeunes, scrape_linkedin_ci

print("🔄 Début du scraping...")
print("\n📍 Scraping AEJI (Agence Emploi Jeunes CI)...")
jobs_aeji = scrape_agenceemploijeunes(max_pages=2)
print(f"✓ {len(jobs_aeji)} offres AEJI scrapées")

print("\n💼 Scraping LinkedIn...")
jobs_linkedin = scrape_linkedin_ci(keyword="Côte d'Ivoire", max_results=30)
print(f"✓ {len(jobs_linkedin)} offres LinkedIn scrapées")

print(f"\n✅ Total : {len(jobs_aeji) + len(jobs_linkedin)} offres ajoutées à la base!")
print("\n📌 Accès aux offres :")
print("   • Page d'offres : http://127.0.0.1:8000/jobs/")
print("   • Admin : http://127.0.0.1:8000/admin/jobs/job/")
print("   • phpMyAdmin : http://localhost/phpmyadmin → jobs_job")
