#!/usr/bin/env python
"""
Script pour nettoyer les URLs invalides des offres scrapées.
Vérifie chaque URL et la supprime si elle retourne un 404 ou timeout.
"""
import os
import django
import requests
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
django.setup()

from jobs.models import Job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

def cleanup_invalid_urls():
    """Nettoie les URLs invalides."""
    jobs = Job.objects.filter(source_type='scraping', external_url__isnull=False).exclude(external_url='')
    
    invalid_count = 0
    valid_count = 0
    
    for job in jobs:
        url = job.external_url
        try:
            resp = requests.head(url, headers=HEADERS, timeout=5, allow_redirects=True)
            if resp.status_code >= 400:
                logger.warning(f'❌ INVALID: HTTP {resp.status_code} - {url}')
                job.external_url = ''  # Vider l'URL invalide
                job.save(update_fields=['external_url'])
                invalid_count += 1
            else:
                valid_count += 1
                logger.info(f'✅ VALID: HTTP {resp.status_code} - {url}')
        except requests.Timeout:
            logger.warning(f'⏱️ TIMEOUT: {url}')
            job.external_url = ''
            job.save(update_fields=['external_url'])
            invalid_count += 1
        except Exception as e:
            logger.warning(f'⚠️ ERROR: {url} - {e}')
            # Ne pas la supprimer, c'est peut-être un problème temporaire
    
    logger.info(f'\n📊 Résumé:')
    logger.info(f'   URLs valides: {valid_count}')
    logger.info(f'   URLs invalides supprimées: {invalid_count}')

if __name__ == '__main__':
    cleanup_invalid_urls()
