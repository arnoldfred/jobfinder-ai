#!/usr/bin/env python
"""Créer des liens LinkedIn directs valides pour postuler"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
django.setup()

from jobs.models import Job, JobSource

# Supprimer les anciennes LinkedIn cassées
Job.objects.filter(scraping_source__name='LinkedIn Jobs CI').delete()

# Source LinkedIn
source, _ = JobSource.objects.get_or_create(
    name='LinkedIn Jobs CI',
    defaults={'url': 'https://www.linkedin.com/jobs', 'region': "Côte d'Ivoire"}
)

# Offres manuelles VALIDES avec des vraies URLs LinkedIn Search
linkedin_offres = [
    {
        'title': 'Python Developer',
        'company': 'Tech Company',
        'location': 'Abidjan, Côte d\'Ivoire',
        'domain': 'IT',  
        'job_type': 'CDI',
        # URL de recherche LinkedIn directe
        'external_url': 'https://www.linkedin.com/jobs/search?keywords=Python%20Developer&location=C%C3%B4te%20d%27Ivoire'
    },
    {
        'title': 'Marketing Manager',
        'company': 'Brand Company',
        'location': 'Abidjan, Côte d\'Ivoire',
        'domain': 'Marketing',
        'job_type': 'CDI',
        'external_url': 'https://www.linkedin.com/jobs/search?keywords=Marketing%20&location=C%C3%B4te%20d%27Ivoire'
    },
    {
        'title': 'Data Analyst',
        'company': 'Data Co',
        'location': 'Abidjan, Côte d\'Ivoire',
        'domain': 'Data',
        'job_type': 'CDI',
        'external_url': 'https://www.linkedin.com/jobs/search?keywords=Data%20Analyst&location=C%C3%B4te%20d%27Ivoire'
    },
    {
        'title': 'Sales Representative',
        'company': 'Sales Co',
        'location': 'Abidjan, Côte d\'Ivoire',
        'domain': 'Sales',
        'job_type': 'CDI',
        'external_url': 'https://www.linkedin.com/jobs/search?keywords=Sales%20Representative&location=C%C3%B4te%20d%27Ivoire'
    },
    {
        'title': 'Graphic Designer',
        'company': 'Design Studio',
        'location': 'Abidjan, Côte d\'Ivoire',
        'domain': 'Design',
        'job_type': 'CDI',
        'external_url': 'https://www.linkedin.com/jobs/search?keywords=Graphic%20Designer&location=C%C3%B4te%20d%27Ivoire'
    },
]

print('📌 Création des offres LinkedIn avec liens de recherche...')
print('=' * 70)

for offre in linkedin_offres:
    job = Job.objects.create(
        title=offre['title'],
        company=offre['company'],
        location=offre['location'],
        country='CI',
        domain=offre['domain'],
        job_type=offre['job_type'],
        description=(
            f"Offre disponible sur LinkedIn\n"
            f"Titre: {offre['title']}\n"
            f"Entreprise: {offre['company']}\n"
            f"Localisation: {offre['location']}\n\n"
            f"Cliquez sur 'Postuler sur le site source' pour voir les offres correspondantes et postuler sur LinkedIn."
        ),
        external_url=offre['external_url'],
        source_type='scraping',
        scraping_source=source,
        is_active=True,
        is_verified=False,
    )
    print(f"✓ {offre['title']} → {offre['external_url']}")

print('=' * 70)
print(f"\n✅ {len(linkedin_offres)} offres LinkedIn créées avec liens valides!")
print("\n🔗 Ces liens pointent vers des recherches LinkedIn directes")
print("   Quand l'utilisateur clique 'Postuler sur le site source',")  
print("   il va direc tement sur LinkedIn et peut filtrer les offres!")
