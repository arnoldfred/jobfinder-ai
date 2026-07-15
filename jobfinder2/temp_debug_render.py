import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','jobfinder.settings')
import django
django.setup()
from django.test import RequestFactory
from django.contrib.auth import get_user_model
import jobs.views as views
from django.http import HttpResponse

saved = {}
def fake_render(request, template_name, context=None, content_type=None, status=None, using=None):
    saved['template'] = template_name
    saved['context'] = context
    return HttpResponse('OK')

views.render = fake_render

User = get_user_model()
user = User.objects.filter(email__icontains='arnoldfreddyadopo').first()
if not user:
    raise SystemExit('User not found')
rf = RequestFactory()
request = rf.get('/jobs/', {'sort': 'score'})
request.user = user
request.session = {}
request.COOKIES = {}
request.META['HTTP_HOST'] = '127.0.0.1'

response = views.job_list(request)
print('response status', response.status_code)
print('template', saved.get('template'))
ctx = saved.get('context')
print('context keys', list(ctx.keys()))
print('sort filter', ctx['filters']['sort'])
print('first 20 jobs:')
for idx, item in enumerate(ctx['jobs_data'][:20], start=1):
    j = item['job']
    print(idx, j.pk, j.title, item['score'], j.source_type, j.posted_at)
