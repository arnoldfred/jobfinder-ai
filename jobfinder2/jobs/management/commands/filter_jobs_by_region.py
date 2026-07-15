"""
Django Management Command: Filtre et améliore les offres d'emploi par région
Removes jobs not matching Côte d'Ivoire / West African criteria
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
django.setup()

from django.core.management.base import BaseCommand
from jobs.models import Job
import logging

logger = logging.getLogger(__name__)

# Régions et pays à garder
VALID_CITIES = [
    'abidjan', 'yamoussoukro', 'bouaké', 'daloa', 'gagnoa', 'korhogo',
    'san-pédro', 'duekoué', 'soubré', 'man', 'odienné', 'katiola',
]

VALID_COUNTRIES = ['ci', 'côte d\'ivoire', 'ivory coast', 'cote d\'ivoire', 'cote divoire']

VALID_REGIONS = [
    'côte d\'ivoire', 'ivory coast', 'west africa', 'afrique de l\'ouest',
    'senegal', 'ghana', 'benin', 'togo', 'burkina faso',
    'mali', 'niger', 'liberia', 'sierra leone', 'guinea',
]

# Régions à rejeter
REJECT_COUNTRIES = [
    'usa', 'united states', 'france', 'paris', 'london', 'uk', 'united kingdom',
    'canada', 'australia', 'new york', 'california', 'toronto',
    'madrid', 'berlin', 'amsterdam', 'singapore', 'dubai', 'hong kong',
    'india', 'brazil', 'mexico',
]


def is_valid_location(location_text):
    """
    Vérifie si une localisation correspond à Côte d'Ivoire ou Afrique Ouest.
    Retourne (is_valid, is_definitely_invalid)
    """
    if not location_text:
        return False, False
    
    loc_lower = location_text.lower().strip()
    
    # Vérifier les rejets explicites
    for reject_kw in REJECT_COUNTRIES:
        if reject_kw in loc_lower:
            return False, True
    
    # Vérifier les acceptations
    for accept_kw in VALID_CITIES + VALID_COUNTRIES + VALID_REGIONS:
        if accept_kw in loc_lower:
            return True, False
    
    # "Remote" est acceptable si combiné avec CI
    if 'remote' in loc_lower:
        if any(ci_kw in loc_lower for ci_kw in ['ci', 'ivory', 'côte']):
            return True, False
        # Remote seul = probablement international
        return False, False
    
    # Ambiguë (ne pas rejeter, pero flag pour review)
    return False, False


class Command(BaseCommand):
    help = 'Filtre les offres d\'emploi par région (Côte d\'Ivoire / Afrique Ouest)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Afficher les changements sans les appliquer'
        )
        parser.add_argument(
            '--source',
            type=str,
            help='Filtrer une source spécifique (ex: "LinkedIn Jobs CI")'
        )
        parser.add_argument(
            '--remove-invalid',
            action='store_true',
            help='Supprimer les offres invalides (au lieu de les désactiver)'
        )
    
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        source_name = options.get('source')
        remove_invalid = options.get('remove_invalid', False)
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Filtrage des offres par région'))
        self.stdout.write(
            self.style.WARNING(f"Mode: {'DRY RUN' if dry_run else 'MISE À JOUR RÉELLE'}")
        )
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # Récupérer les offres
        jobs = Job.objects.filter(is_active=True)
        if source_name:
            jobs = jobs.filter(scraping_source__name=source_name)
        
        total = jobs.count()
        self.stdout.write(f"Offres à vérifier: {total}")
        
        valid_jobs = []
        invalid_jobs = []
        ambiguous_jobs = []
        
        for idx, job in enumerate(jobs, 1):
            if idx % 50 == 0:
                self.stdout.write(f"Progression: {idx}/{total}...")
            
            location = job.location or ''
            is_valid, is_rejected = is_valid_location(location)
            
            if is_valid:
                valid_jobs.append(job)
            elif is_rejected:
                invalid_jobs.append(job)
            else:
                ambiguous_jobs.append(job)
        
        # Rapport
        self.stdout.write('\n' + self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('RAPPORT'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f"✓ Offres valides: {len(valid_jobs)}"))
        self.stdout.write(self.style.WARNING(f"? Offres ambiguës: {len(ambiguous_jobs)}"))
        self.stdout.write(self.style.ERROR(f"✗ Offres invalides: {len(invalid_jobs)}"))
        
        # Détail des invalides
        if invalid_jobs:
            self.stdout.write('\n' + self.style.ERROR('Offres rejetées:'))
            for job in invalid_jobs[:10]:  # Top 10
                self.stdout.write(
                    f"  ✗ {job.title[:40]} — {job.location} (source: {job.scraping_source.name})"
                )
            if len(invalid_jobs) > 10:
                self.stdout.write(f"  ... et {len(invalid_jobs) - 10} autres")
        
        # Détail des ambiguës
        if ambiguous_jobs:
            self.stdout.write('\n' + self.style.WARNING('Offres à vérifier manuellement:'))
            for job in ambiguous_jobs[:5]:
                self.stdout.write(
                    f"  ? {job.title[:40]} — {job.location} (source: {job.scraping_source.name})"
                )
            if len(ambiguous_jobs) > 5:
                self.stdout.write(f"  ... et {len(ambiguous_jobs) - 5} autres")
        
        # Action
        if invalid_jobs:
            if remove_invalid:
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f"\n[DRY RUN] {len(invalid_jobs)} offres SERAIENT supprimées"
                        )
                    )
                else:
                    self.stdout.write(f"\nSuppression de {len(invalid_jobs)} offres...")
                    for job in invalid_jobs:
                        job.delete()
                        logger.info(f"Supprimée: {job.external_id}")
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ {len(invalid_jobs)} offres supprimées")
                    )
            else:
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f"\n[DRY RUN] {len(invalid_jobs)} offres SERAIENT désactivées"
                        )
                    )
                else:
                    self.stdout.write(f"\nDésactivation de {len(invalid_jobs)} offres...")
                    for job in invalid_jobs:
                        job.is_active = False
                        job.save(update_fields=['is_active'])
                        logger.info(f"Désactivée: {job.external_id}")
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ {len(invalid_jobs)} offres désactivées")
                    )
        
        # Résumé final
        self.stdout.write('\n' + self.style.SUCCESS('=' * 60))
        self.stdout.write(
            self.style.SUCCESS(
                f"Résultat: {len(valid_jobs)} offres valides pour Côte d'Ivoire"
            )
        )
        if ambigiuous_jobs:
            self.stdout.write(
                self.style.WARNING(
                    f"Vérifiez {len(ambiguous_jobs)} offres ambiguës manuellement"
                )
            )
        self.stdout.write(self.style.SUCCESS('=' * 60))
