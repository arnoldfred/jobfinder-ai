import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from jobs.models import Job, JobMatch
from applications.models import Application
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
print('DATA ANALYST jobs:')
for job in Job.objects.filter(title__icontains='DATA ANALYST'):
    print('JOB', job.pk, job.title, job.source_type, job.employer_id, job.is_active, job.posted_at, job.salary_text)
    bm = JobMatch.objects.filter(user=user, job=job).first()
    print('  JOBMATCH score:', bm.score if bm else None)
    app_count = Application.objects.filter(user=user, job=job).count()
    print('  APPLIED:', app_count)
