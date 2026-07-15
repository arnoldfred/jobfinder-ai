#!/usr/bin/env python
"""
Script de Maintenance Complète — JobFinder AI
Exécute tous les checks et cleanups d'un coup

Usage:
    python maintenance_complete.py
    python maintenance_complete.py --linkedin-only
    python maintenance_complete.py --clean-old 30
"""
import os
import sys
import django
import argparse
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
django.setup()

from django.utils import timezone
from jobs.models import Job, JobSource
import subprocess
from datetime import datetime

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(f'logs/maintenance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def print_header(title):
    """Affiche un header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def run_command(cmd, description):
    """Exécute une commande Django management"""
    print(f"\n→ {description}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {description} — OK")
            logger.info(f"✓ {description}")
            return True
        else:
            print(f"✗ {description} — ERREUR")
            print(result.stderr)
            logger.error(f"✗ {description}: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Erreur exécution: {e}")
        logger.error(f"✗ Erreur: {e}")
        return False


def maintenance_complete(
    scrape_linkedin=True,
    filter_region=True,
    check_dead_links=True,
    clean_old_days=None,
    dry_run=False
):
    """
    Exécute la maintenance complète
    """
    print_header("JOBFINDER AI — MAINTENANCE COMPLÈTE")
    print(f"Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY RUN' if dry_run else 'PRODUCTION'}")
    
    results = {
        'started_at': timezone.now(),
        'completed_tasks': [],
        'failed_tasks': [],
        'summary': {}
    }
    
    # 1. SCRAPING LINKEDIN
    if scrape_linkedin:
        print_header("ÉTAPE 1: SCRAPING LINKEDIN")
        cmd = ['python', 'manage.py', 'scrape_jobs']
        if dry_run:
            cmd.append('--dry-run')
        
        if run_command(cmd, "Scraping LinkedIn"):
            results['completed_tasks'].append('scrape_linkedin')
            
            # Stats
            source = JobSource.objects.filter(name='LinkedIn Jobs CI').first()
            if source:
                results['summary']['linkedin_jobs'] = Job.objects.filter(
                    scraping_source=source,
                    is_active=True
                ).count()
                results['summary']['linkedin_last_sync'] = source.last_sync
        else:
            results['failed_tasks'].append('scrape_linkedin')
    
    # 2. FILTRAGE PAR RÉGION
    if filter_region:
        print_header("ÉTAPE 2: FILTRAGE PAR RÉGION")
        cmd = ['python', 'manage.py', 'filter_jobs_by_region']
        if dry_run:
            cmd.append('--dry-run')
        
        if run_command(cmd, "Filtrage régional"):
            results['completed_tasks'].append('filter_region')
            
            # Stats
            results['summary']['active_ci_jobs'] = Job.objects.filter(
                is_active=True,
                country='CI'
            ).count()
        else:
            results['failed_tasks'].append('filter_region')
    
    # 3. VÉRIFIER LES LIENS MORTS
    if check_dead_links:
        print_header("ÉTAPE 3: VÉRIFICATION DES LIENS MORTS")
        try:
            from check_and_clean_dead_links import check_and_clean_dead_links
            
            result = check_and_clean_dead_links(dry_run=dry_run)
            print(f"✓ Vérification des liens — OK")
            print(f"  Liens valides: {result['valid']}")
            print(f"  Liens morts: {result['dead']}")
            
            results['completed_tasks'].append('check_dead_links')
            results['summary'].update({
                'valid_links': result['valid'],
                'dead_links': result['dead']
            })
            
            logger.info(f"✓ Vérification des liens")
        except Exception as e:
            print(f"✗ Erreur vérification liens: {e}")
            results['failed_tasks'].append('check_dead_links')
            logger.error(f"✗ Erreur vérification: {e}")
    
    # 4. NETTOYER LES VIEILLES OFFRES
    if clean_old_days:
        print_header(f"ÉTAPE 4: NETTOYAGE (offres inactives > {clean_old_days} jours)")
        try:
            from check_and_clean_dead_links import clean_old_inactive_jobs
            
            if not dry_run:
                clean_old_inactive_jobs(days=clean_old_days)
                print(f"✓ Nettoyage des vieilles offres — OK")
            else:
                print(f"[DRY RUN] Nettoyage aurait lieu pour offres > {clean_old_days} jours")
            
            results['completed_tasks'].append('clean_old')
            logger.info(f"✓ Nettoyage des vieilles offres")
        except Exception as e:
            print(f"✗ Erreur nettoyage: {e}")
            results['failed_tasks'].append('clean_old')
            logger.error(f"✗ Erreur nettoyage: {e}")
    
    # RÉSUMÉ FINAL
    print_header("RÉSUMÉ FINAL")
    print(f"Tâches réussies: {len(results['completed_tasks'])}")
    for task in results['completed_tasks']:
        print(f"  ✓ {task}")
    
    if results['failed_tasks']:
        print(f"\nTâches échouées: {len(results['failed_tasks'])}")
        for task in results['failed_tasks']:
            print(f"  ✗ {task}")
    
    print(f"\nStatistiques:")
    for key, value in results['summary'].items():
        if isinstance(value, datetime):
            print(f"  {key}: {value.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"  {key}: {value}")
    
    results['completed_at'] = timezone.now()
    duration = (results['completed_at'] - results['started_at']).total_seconds()
    print(f"\nDurée totale: {duration:.1f}s")
    print("=" * 70)
    
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Maintenance complète JobFinder AI'
    )
    parser.add_argument('--linkedin-only', action='store_true',
                       help='Scraper LinkedIn seulement')
    parser.add_argument('--filter-only', action='store_true',
                       help='Filtrer par région seulement')
    parser.add_argument('--check-links-only', action='store_true',
                       help='Vérifier les liens seulement')
    parser.add_argument('--clean-old', type=int, metavar='DAYS',
                       help='Nettoyer les offres inactives depuis N jours')
    parser.add_argument('--dry-run', action='store_true',
                       help='Afficher sans modifier')
    
    args = parser.parse_args()
    
    # Déterminer quelles tâches exécuter
    scrape = not (args.filter_only or args.check_links_only)
    filter_region = not (args.linkedin_only or args.check_links_only)
    check_links = not (args.linkedin_only or args.filter_only)
    
    if args.linkedin_only:
        scrape, filter_region, check_links = True, False, False
    elif args.filter_only:
        scrape, filter_region, check_links = False, True, False
    elif args.check_links_only:
        scrape, filter_region, check_links = False, False, True
    
    # Exécuter
    result = maintenance_complete(
        scrape_linkedin=scrape,
        filter_region=filter_region,
        check_dead_links=check_links,
        clean_old_days=args.clean_old,
        dry_run=args.dry_run
    )
    
    # Exit code
    sys.exit(0 if not result['failed_tasks'] else 1)
