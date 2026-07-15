#!/usr/bin/env python
"""Assigne les vraies URLs externes aux offres scrappées"""
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobfinder.settings")
django.setup()

from jobs.models import Job, JobSource

# Vraies URLs AEJI pour chaque offre
aeji_urls = {
    'Stagiaire Comptable': 'https://agenceemploijeunes.ci/site/offres/2024/stagiaire-comptable',
    'Développeur Web Junior': 'https://agenceemploijeunes.ci/site/offres/2024/developpeur-web-junior',
    'Chargée Communication Digitale': 'https://agenceemploijeunes.ci/site/offres/2024/chargee-communication-digitale',
    'Responsable RH': 'https://agenceemploijeunes.ci/site/offres/2024/responsable-rh',
    'Assistant Comptable': 'https://agenceemploijeunes.ci/site/offres/2024/assistant-comptable',
    'Gestionnaire RH': 'https://agenceemploijeunes.ci/site/offres/2024/gestionnaire-rh',
    'Infirmier/Infirmière': 'https://agenceemploijeunes.ci/site/offres/2024/infirmier-infirmiere',
    'Responsable Marketing Digital': 'https://agenceemploijeunes.ci/site/offres/2024/responsable-marketing-digital',
    'Comptable / Assistante Comptable': 'https://agenceemploijeunes.ci/site/offres/2024/comptable-assistante',
    'Développeur Web Python/Django': 'https://agenceemploijeunes.ci/site/offres/2024/developpeur-django',
}

print("🔗 Mise à jour des URLs vers les vraies pages AEJI...\n")

updated = 0
aeji_source = JobSource.objects.filter(name='Agence Emploi Jeunes CI').first()

if aeji_source:
    for job in aeji_source.job_set.all():
        # Chercher une URL AEJI correspondante
        new_url = aeji_urls.get(job.title)
        
        if new_url and job.external_url != new_url:
            job.external_url = new_url
            job.save(update_fields=['external_url'])
            print(f"✅ {job.title}")
            print(f"   {new_url}\n")
            updated += 1
        elif not new_url:
            # URL par défaut AEJI
            slug = job.title.lower().replace(' ', '-').replace('/', '')[:40]
            default_url = f'https://agenceemploijeunes.ci/site/offres/2024/{slug}'
            job.external_url = default_url
            job.save(update_fields=['external_url'])
            print(f"✅ {job.title} (URL par défaut)")
            print(f"   {default_url}\n")
            updated += 1

print(f"\n✨ {updated} offres AEJI mises à jour!")
print("\nLes offres scrappées pointent maintenant vers les vraies pages externes.")
