"""python manage.py scrape_jobs"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Scrape les offres d'emploi ivoiriennes (AEJI + Abidjan.net)"

    def add_arguments(self, parser):
        parser.add_argument('--source', choices=['aeji','abidjannet','linkedin','all'], default='all')
        parser.add_argument('--pages',  type=int, default=5)
        parser.add_argument('--max',    type=int, default=50)
        parser.add_argument('--cleanup', action='store_true',
                            help='Désactiver offres > 60j')
        parser.add_argument('--match',  action='store_true',
                            help='Recalculer matching après scraping')

    def handle(self, *args, **options):
        from jobs.scraper import scrape_agenceemploijeunes, scrape_abidjannet, cleanup_expired_jobs

        src   = options['source']
        total = 0

        self.stdout.write(self.style.HTTP_INFO('\nJobFinder AI — Scraping\n'))

        if src in ('aeji', 'all'):
            self.stdout.write('>> agenceemploijeunes.ci ...')
            try:
                jobs = scrape_agenceemploijeunes(max_pages=options['pages'])
                total += len(jobs)
                self.stdout.write(self.style.SUCCESS(f'   OK {len(jobs)} offres AEJI'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ERREUR {e}'))

        if src in ('abidjannet', 'linkedin', 'all'):
            self.stdout.write('>> annonces.abidjan.net ...')
            try:
                jobs = scrape_abidjannet(max_pages=options['pages'])
                total += len(jobs)
                self.stdout.write(self.style.SUCCESS(f'   OK {len(jobs)} offres Abidjan.net'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ERREUR {e}'))

        if options['cleanup']:
            n = cleanup_expired_jobs(days=60)
            self.stdout.write(self.style.WARNING(f'   🧹 {n} offres expirées désactivées'))

        if options['match'] and total > 0:
            self.stdout.write('⚙️  Recalcul matching ...')
            try:
                from jobs.matching import bulk_compute_matches
                from jobs.models import Job
                from django.contrib.auth import get_user_model
                User = get_user_model()
                new_jobs = list(Job.objects.filter(is_active=True).order_by('-posted_at')[:50])
                for user in User.objects.filter(role='jobseeker', is_active=True)[:100]:
                    try:
                        bulk_compute_matches(user, jobs=new_jobs)
                    except Exception:
                        pass
                self.stdout.write(self.style.SUCCESS('   ✓ Matching recalculé'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ✗ {e}'))

        msg = f'✅ {total} nouvelles offres' if total else '⚠ Aucune nouvelle offre'
        self.stdout.write(self.style.SUCCESS(msg) if total else self.style.WARNING(msg))
