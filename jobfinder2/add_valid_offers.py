#!/usr/bin/env python
"""
Ajouter des vraies offres d'emploi avec des liens valides pour CI
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

from jobs.models import Job, JobSource
from django.utils import timezone
from datetime import timedelta

# Source AEJI valide
aeji_source, _ = JobSource.objects.get_or_create(
    name='Agence Emploi Jeunes CI',
    defaults={
        'url': 'https://agenceemploijeunes.ci/site',
        'region': "Côte d'Ivoire"
    }
)

# Source LinkedIn valide
linkedin_source, _ = JobSource.objects.get_or_create(
    name='LinkedIn Jobs CI',
    defaults={
        'url': 'https://www.linkedin.com/jobs',
        'region': "Côte d'Ivoire"
    }
)

# Vraies offres avec des liens directs valides
offres_reelles = [
    # AEJI - Offres génériques d'emploi sur AEJI
    {
        'title': 'Offres d\'emploi - Agence Emploi Jeunes CI',
        'company': 'Agence Emploi Jeunes CI',
        'location': 'Abidjan',
        'country': 'CI',
        'external_url': 'https://agenceemploijeunes.ci/site',
        'description': 'Découvrez toutes les offres d\'emploi disponibles sur le site de l\'Agence Emploi Jeunes Côte d\'Ivoire. Offres en permanence mises à jour.',
        'source': aeji_source,
    },
    # LinkedIn - Recherches d'emploi par catégorie
    {
        'title': 'Emplois Informatique & Tech - LinkedIn',
        'company': 'LinkedIn',
        'location': 'Côte d\'Ivoire',
        'country': 'CI',
        'external_url': 'https://www.linkedin.com/jobs/search?keywords=informatique%20tech&location=C%C3%B4te%20d%27Ivoire',
        'description': 'Offres d\'emploi en informatique et technologies en Côte d\'Ivoire sur LinkedIn.',
        'source': linkedin_source,
    },
    {
        'title': 'Emplois Marketing & Ventes - LinkedIn',
        'company': 'LinkedIn',
        'location': 'Côte d\'Ivoire',
        'country': 'CI',
        'external_url': 'https://www.linkedin.com/jobs/search?keywords=marketing%20ventes&location=C%C3%B4te%20d%27Ivoire',
        'description': 'Offres d\'emploi en marketing et ventes en Côte d\'Ivoire sur LinkedIn.',
        'source': linkedin_source,
    },
    {
        'title': 'Emplois Finance & Comptabilité - LinkedIn',
        'company': 'LinkedIn',
        'location': 'Côte d\'Ivoire',
        'country': 'CI',
        'external_url': 'https://www.linkedin.com/jobs/search?keywords=finance%20comptabilit%C3%A9&location=C%C3%B4te%20d%27Ivoire',
        'description': 'Offres d\'emploi en finance et comptabilité en Côte d\'Ivoire sur LinkedIn.',
        'source': linkedin_source,
    },
    {
        'title': 'Emplois Ressources Humaines - LinkedIn',
        'company': 'LinkedIn',
        'location': 'Côte d\'Ivoire',
        'country': 'CI',
        'external_url': 'https://www.linkedin.com/jobs/search?keywords=ressources%20humaines&location=C%C3%B4te%20d%27Ivoire',
        'description': 'Offres d\'emploi en ressources humaines en Côte d\'Ivoire sur LinkedIn.',
        'source': linkedin_source,
    },
]

print('➕ Ajout de vraies offres avec des liens valides...\n')

for offer in offres_reelles:
    job, created = Job.objects.get_or_create(
        external_id=f"{offer['source'].name.lower().replace(' ', '_')}_{offer['title'].lower().replace(' ', '_')[:30]}",
        defaults={
            'title': offer['title'],
            'company': offer['company'],
            'location': offer['location'],
            'country': offer['country'],
            'external_url': offer['external_url'],
            'description': offer['description'],
            'scraping_source': offer['source'],
            'source_type': 'scraping',
            'job_type': 'CDI',
            'is_active': True,
            'posted_at': timezone.now(),
        }
    )
    
    if created:
        print(f'✅ Créé: {job.title}')
        print(f'   Lien: {job.external_url}\n')
    else:
        print(f'ℹ️  Existe déjà: {job.title}\n')

print('✅ Offres ajoutées avec succès!')
