import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','jobfinder.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from jobs.models import Job, JobMatch
from jobs.views import _cached_score
from jobs.matching import compute_display_score
from django.utils import timezone
from applications.models import Application

User = get_user_model()
user = User.objects.filter(email__icontains='arnoldfreddyadopo').first()
if not user:
    raise SystemExit('User not found')

applied_ids=set(Application.objects.filter(user=user).values_list('job_id', flat=True))
qs = Job.objects.filter(is_active=True).exclude(id__in=applied_ids)
all_jobs=list(qs)
match_map={}
for job in all_jobs:
    base_score,_ = _cached_score(user, job)
    score = compute_display_score(user, job, base_score=base_score)
    match_map[job.id] = score

print('before sort')
for j in all_jobs[:20]:
    print(j.id, match_map[j.id], j.posted_at)

all_jobs.sort(
    key=lambda j: (
        match_map.get(j.id, 0),
        j.posted_at or timezone.datetime.min.replace(tzinfo=timezone.utc),
        j.id,
    ),
    reverse=True,
)

print('\nafter sort')
for j in all_jobs[:20]:
    print(j.id, match_map[j.id], j.posted_at)

print('\nfirst 20 results from sort')
for idx,j in enumerate(all_jobs[:20], start=1):
    print(idx, j.id, j.title, match_map[j.id], j.source_type, j.posted_at)
