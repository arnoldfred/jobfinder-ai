#!/usr/bin/env python
"""Mettre à jour les liens d'offres vers les routes internes de postulation"""
import os
import sys
import django
from django.urls import reverse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobfinder.settings")
django.setup()

from jobs.models import Job

print("🔄 Mise à jour des liens de postulation...\n")

updated = 0
for job in Job.objects.all():
    # Tous les liens pointent vers le formulaire de postulation interne
    new_url = f'http://127.0.0.1:8000/jobs/{job.pk}/apply/'
    
    if job.external_url != new_url:
        job.external_url = new_url
        job.save(update_fields=['external_url'])
        print(f"✅ {job.title}")
        print(f"   🔗 {new_url}\n")
        updated += 1
    else:
        print(f"⏭️  {job.title} (déjà à jour)")

print(f"\n✨ {updated} offres mises à jour!")
print("\n📍 Testez maintenant: http://127.0.0.1:8000/jobs/")
