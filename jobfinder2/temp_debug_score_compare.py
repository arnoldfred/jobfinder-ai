import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','jobfinder.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from jobs.models import Job, JobMatch
from jobs.matching import compute_display_score
from jobs.views import _cached_score
from applications.models import Application

User = get_user_model()
user = User.objects.filter(email__icontains='arnoldfreddyadopo').first()
if not user:
    raise SystemExit('User not found')

job_ids = [11, 42]
for jid in job_ids:
    job = Job.objects.get(pk=jid)
    base, _ = _cached_score(user, job)
    list_score = compute_display_score(user, job, base_score=base, refresh_base=True)
    detail_score = compute_display_score(user, job, base_score=base, refresh_base=True)
    print('job', jid, job.title, 'base', base, 'list', list_score, 'detail', detail_score)
