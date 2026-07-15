import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','jobfinder.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from jobs.models import Job, JobMatch
from jobs.matching import compute_display_score

User = get_user_model()
print('Users with Data Analyst matches at 91:')
for jm in JobMatch.objects.filter(score=91).select_related('user', 'job')[:50]:
    print(jm.user.email, jm.job.pk, jm.job.title, jm.job.source_type, jm.job.posted_at)

print('\nAll Data Analyst jobs with computed display score >= 80:')
for job in Job.objects.filter(title__icontains='data analyst').order_by('-posted_at')[:50]:
    # might not have a match for every user
    jm = JobMatch.objects.filter(job=job).first()
    print(job.pk, job.title, jm.score if jm else None, job.source_type, job.posted_at)
