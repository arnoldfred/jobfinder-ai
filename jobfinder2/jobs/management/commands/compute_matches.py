"""python manage.py compute_matches  —  NLP TF-IDF matching"""
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Compute NLP match scores (TF-IDF cosine similarity) between candidates and jobs'

    def add_arguments(self, parser):
        parser.add_argument('--user', type=int, help='Calculer pour un user specifique (id)', default=None)
        parser.add_argument('--limit', type=int, default=50, help='Nombre max d offres a traiter')

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model
        from jobs.models import Job
        from jobs.matching import compute_match_score, bulk_compute_matches
        from jobs.models import JobMatch

        User  = get_user_model()
        limit = options['limit']

        if options['user']:
            users = User.objects.filter(pk=options['user'], role='jobseeker')
        else:
            users = User.objects.filter(is_active=True, role='jobseeker')

        jobs  = list(Job.objects.filter(is_active=True)[:limit])
        total = 0

        self.stdout.write('Calcul NLP matching pour %d candidats × %d offres...' % (users.count(), len(jobs)))

        for user in users:
            try:
                results = bulk_compute_matches(user, jobs=jobs, limit=limit)
                total  += len(results)
                if results:
                    top = results[0]
                    self.stdout.write('  %s — meilleur: %s (%d%%)' % (
                        user.email, top['job'].title[:40], top['detail']['score']))
            except Exception as e:
                self.stdout.write(self.style.WARNING('  Erreur %s: %s' % (user.email, e)))

        self.stdout.write(self.style.SUCCESS('Matching termine: %d scores calcules' % total))
