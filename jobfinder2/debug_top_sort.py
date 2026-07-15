import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from jobs.models import Job, JobMatch
from applications.models import Application
from jobs.matching import compute_display_score
from django.db.models import Q
User = get_user_model()
user = User.objects.filter(email__icontains='arnoldfreddyadopo').first()
print('USER:', user)
if not user:
    user = User.objects.filter(Q(first_name__icontains='Arnold') | Q(last_name__icontains='Freddy')).first()
    print('FALLBACK USER:', user)
if not user:
    raise SystemExit('User not found')
print('Using user:', user.pk, user.email)
print('is_employer:', getattr(user, 'is_employer', None), 'is_authenticated:', user.is_authenticated)

applied_ids = set(Application.objects.filter(user=user).values_list('job_id', flat=True))
all_jobs = Job.objects.filter(is_active=True).exclude(id__in=applied_ids)
results = []
for job in all_jobs:
    base_score = JobMatch.objects.filter(user=user, job=job).values_list('score', flat=True).first() or 0
    score = compute_display_score(user, job, base_score=base_score)
    results.append((score, job.posted_at, job.source_type, job.id, job.title[:80]))
results.sort(key=lambda x: (x[0], x[1]), reverse=True)
for r in results[:20]:
    print(r)
print('--- total jobs', len(results))
