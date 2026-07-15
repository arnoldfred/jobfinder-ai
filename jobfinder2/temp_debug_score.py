import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','jobfinder.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from jobs.models import Job, JobMatch
from jobs.matching import compute_display_score

User = get_user_model()
user = User.objects.filter(email__icontains='arnoldfreddyadopo').first()
if not user:
    raise SystemExit('User not found')
print('User:', user.pk, user.email)

for job_id in [11, 42]:
    try:
        job = Job.objects.get(pk=job_id)
    except Job.DoesNotExist:
        print('job missing', job_id)
        continue
    bm = JobMatch.objects.filter(user=user, job=job).first()
    base = bm.score if bm else None
    display = compute_display_score(user, job, base_score=base if base is not None else 0)
    print('job', job.pk, job.title, job.source_type, job.posted_at, 'base', base, 'display', display)

print('\nTop 20 sorted by display score:')
from applications.models import Application
applied_ids = set(Application.objects.filter(user=user).values_list('job_id', flat=True))
all_jobs = Job.objects.filter(is_active=True).exclude(id__in=applied_ids)
results = []
for job in all_jobs:
    bm = JobMatch.objects.filter(user=user, job=job).first()
    base = bm.score if bm else 0
    display = compute_display_score(user, job, base_score=base)
    results.append((display, job.posted_at, job.pk, job.title))
for r in sorted(results, key=lambda x: (x[0], x[1]), reverse=True)[:30]:
    print(r)
