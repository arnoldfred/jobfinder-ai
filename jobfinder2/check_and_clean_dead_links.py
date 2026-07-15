#!/usr/bin/env python
"""
Script de maintenance: Vérifiez et nettoyez les offres d'emploi avec des liens morts.
- Valide tous les liens externes
- Marque les offres avec des liens morts comme inactives
- Génère un rapport d'offres supprimées

Usage:
    python check_and_clean_dead_links.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
django.setup()

import requests
from django.utils import timezone
from jobs.models import Job, JobSource
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s — %(levelname)s — %(message)s'
)
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}


def validate_external_url(url, timeout=10):
    """
    Valide qu'une URL externe est accessible.
    Retourne (is_valid, status_code)
    """
    if not url or not url.startswith('http'):
        return False, 0
    
    try:
        resp = requests.head(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        is_valid = resp.status_code == 200
        return is_valid, resp.status_code
    except requests.exceptions.Timeout:
        return False, 0
    except Exception as e:
        logger.warning(f"Validation error for {url}: {e}")
        return False, 0


def check_and_clean_dead_links(source_name=None, dry_run=False):
    """
    Vérifie tous les liens externes et marque les morts comme inactifs.
    
    Args:
        source_name: Optionnel, vérifie seulement une source (ex: "LinkedIn Jobs CI")
        dry_run: Si True, ne sauvegarde pas les changements, affiche seulement
    """
    logger.info("=" * 60)
    logger.info("Vérification des liens morts")
    logger.info(f"Mode: {'DRY RUN (aucun changement)' if dry_run else 'MISE À JOUR RÉELLE'}")
    logger.info("=" * 60)
    
    # Filtrer les offres
    jobs = Job.objects.filter(is_active=True, source_type='scraping')
    if source_name:
        jobs = jobs.filter(scraping_source__name=source_name)
    
    total_jobs = jobs.count()
    logger.info(f"Offres actives à vérifier: {total_jobs}")
    
    dead_links = []
    valid_links = []
    errors = []
    
    for idx, job in enumerate(jobs, 1):
        if idx % 10 == 0:
            logger.info(f"Progression: {idx}/{total_jobs}")
        
        if not job.external_url:
            continue
        
        is_valid, status_code = validate_external_url(job.external_url)
        
        if is_valid:
            valid_links.append(job)
        else:
            dead_links.append({
                'job': job,
                'url': job.external_url,
                'status': status_code
            })
            logger.warning(
                f"LIEN MORT [{status_code}]: {job.title} "
                f"({job.company}) — {job.external_url[:80]}"
            )
        
        if idx % 5 == 0:
            import time
            time.sleep(0.5)  # Rate limiting
    
    # Rapport
    logger.info("\n" + "=" * 60)
    logger.info("RAPPORT")
    logger.info("=" * 60)
    logger.info(f"✓ Liens valides: {len(valid_links)}")
    logger.info(f"✗ Liens morts: {len(dead_links)}")
    logger.info(f"Total: {len(valid_links) + len(dead_links)}")
    
    # Marquer les liens morts comme inactifs
    if dead_links and not dry_run:
        logger.info(f"\nDésactivation de {len(dead_links)} offres...")
        for entry in dead_links:
            job = entry['job']
            job.is_active = False
            job.save(update_fields=['is_active'])
            logger.info(f"  → Désactivée: {job.external_id}")
        logger.info(f"✓ {len(dead_links)} offres marquées comme inactives")
    elif dead_links and dry_run:
        logger.info(f"\n[DRY RUN] {len(dead_links)} offres SERAIENT désactivées:")
        for entry in dead_links:
            logger.info(f"  → {entry['job'].external_id}: {entry['url'][:80]}")
    
    # Détail par source
    logger.info("\n" + "=" * 60)
    logger.info("PAR SOURCE")
    logger.info("=" * 60)
    for source in JobSource.objects.filter(job__is_active=True).distinct():
        source_jobs = jobs.filter(scraping_source=source)
        source_dead = [d for d in dead_links if d['job'].scraping_source == source]
        logger.info(
            f"{source.name}: {source_jobs.count()} offres, "
            f"{len(source_dead)} liens morts"
        )
    
    return {
        'total': total_jobs,
        'valid': len(valid_links),
        'dead': len(dead_links),
        'dead_links': dead_links
    }


def clean_old_inactive_jobs(days=30):
    """
    Supprime les offres inactives depuis plus de N jours.
    Utile pour nettoyer les vieilles données.
    """
    from datetime import timedelta
    from django.utils import timezone
    
    cutoff_date = timezone.now() - timedelta(days=days)
    old_jobs = Job.objects.filter(
        is_active=False,
        updated_at__lt=cutoff_date
    )
    
    count = old_jobs.count()
    logger.info(f"Suppression de {count} offres inactives depuis > {days} jours...")
    
    for job in old_jobs:
        logger.debug(f"  Supprimée: {job.external_id}")
    
    old_jobs.delete()
    logger.info(f"✓ {count} offres supprimées")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Vérifiez et nettoyez les liens morts')
    parser.add_argument('--source', help='Vérifier une source spécifique (ex: "LinkedIn Jobs CI")')
    parser.add_argument('--dry-run', action='store_true', help='Afficher sans modifier')
    parser.add_argument('--clean-old', type=int, metavar='DAYS', 
                       help='Supprimer les offres inactives depuis N jours')
    
    args = parser.parse_args()
    
    # Vérifier les liens
    result = check_and_clean_dead_links(
        source_name=args.source,
        dry_run=args.dry_run
    )
    
    # Nettoyer les vieilles offres
    if args.clean_old:
        clean_old_inactive_jobs(days=args.clean_old)
    
    logger.info("\n" + "=" * 60)
    logger.info("Maintenance terminée")
    logger.info("=" * 60)
