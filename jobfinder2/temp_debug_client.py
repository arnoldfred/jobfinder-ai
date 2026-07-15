import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','jobfinder.settings')
import django
django.setup()
from django.test import Client
from django.contrib.auth import get_user_model
from django.conf import settings

settings.ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
User = get_user_model()
user = User.objects.filter(email__icontains='arnoldfreddyadopo').first()
if not user:
    raise SystemExit('User not found')
client = Client(HTTP_HOST='127.0.0.1')
client.force_login(user)
response = client.get('/jobs/')
print('status', response.status_code)
print('sort param', response.wsgi_request.GET.get('sort'))
if hasattr(response, 'context') and response.context is not None:
    jobs_data = response.context['jobs_data']
    print('jobs_data count', len(jobs_data))
    for idx, item in enumerate(jobs_data[:20], start=1):
        job = item['job']
        print(idx, job.pk, job.title, item['score'], job.source_type, job.posted_at)
else:
    print('No context; maybe template rendering not available')
