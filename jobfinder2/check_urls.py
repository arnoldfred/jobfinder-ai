#!/usr/bin/env python
"""Affiche les URLs des offres actuelles"""
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobfinder.settings")
django.setup()

from jobs.models import Job

print("📋 URLs actuelles des offres:\n")
print("=" * 80)

for job in Job.objects.all():
    source_name = job.scraping_source.name if job.scraping_source else "Manual"
    print(f"\n{job.title}")
    print(f"  Source: {source_name}")
    print(f"  URL: {job.external_url}")

print("\n" + "=" * 80)
