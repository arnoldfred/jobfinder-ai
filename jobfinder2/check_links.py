#!/usr/bin/env python
"""
Vérifier les liens des offres scrapées
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

from jobs.models import Job, JobSource

print('📋 OFFRES ET LEURS LIENS:\n')
for job in Job.objects.filter(is_active=True).select_related('scraping_source')[:15]:
    print(f'Titre: {job.title}')
    print(f'Source: {job.scraping_source.name if job.scraping_source else "N/A"}')
    print(f'Lien: {job.external_url}')
    print(f'Valide: {"✅" if job.external_url and job.external_url.startswith("http") else "❌"}')
    print('-' * 70)
