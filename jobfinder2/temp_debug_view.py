import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','jobfinder.settings')
import django
django.setup()
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from jobs import views
from django.conf import settings

settings.ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
User = get_user_model()
user = User.objects.filter(email__icontains='arnoldfreddyadopo').first()
if not user:
    raise SystemExit('User not found')
rf = RequestFactory()
request = rf.get('/jobs/')
request.user = user
request.session = {}
request.COOKIES = {}
# add middleware attributes if required
request.META['HTTP_HOST'] = '127.0.0.1'

response = views.job_list(request)
print('response type', type(response))
print('response status', getattr(response, 'status_code', None))
if hasattr(response, 'context_data'):
    print('context_data keys', response.context_data.keys())
if hasattr(response, 'context') and response.context is not None:
    ctx = response.context
    print('context jobs_data len', len(ctx['jobs_data']))
    for idx, item in enumerate(ctx['jobs_data'][:20], start=1):
        job = item['job']
        print(idx, job.pk, job.title, item['score'], job.source_type, job.posted_at)
else:
    print('no context available')
