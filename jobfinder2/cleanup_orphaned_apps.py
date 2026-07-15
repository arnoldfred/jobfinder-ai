#!/usr/bin/env python
"""Nettoie les candidatures orphelines (offre supprimée)"""
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobfinder.settings")
django.setup()

from applications.models import Application

# Trouver et afficher les candidatures orphelines
orphaned = Application.objects.filter(job__isnull=True)
count = orphaned.count()

print(f"🗑️  Candidatures orphelines trouvées: {count}\n")

if count > 0:
    for app in orphaned:
        print(f"  - {app.user} → Offre supprimée (postulé le {app.applied_at.date()})")
    
    # Optionnel: supprimer les candidatures orphelines
    orphaned.delete()
    print(f"\n✅ {count} candidatures orphelines supprimées")
else:
    print("✓ Aucune candidature orpheline trouvée")

# Statistiques
print(f"\n📊 Candidatures valides: {Application.objects.filter(job__isnull=False).count()}")
