import os
import json
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from jobs.models import Job
from employers.models import EmployerProfile

backup_path = Path('backup_sqlite.json')
with backup_path.open(encoding='utf-8') as fh:
    data = json.load(fh)

User = get_user_model()

for item in data:
    model = item.get('model')
    fields = item.get('fields', {})
    pk = item.get('pk')

    if model == 'accounts.user':
        email = fields.get('email')
        if not email or User.objects.filter(email=email).exists():
            continue
        user = User(
            pk=pk,
            username=fields.get('username') or email,
            email=email,
            first_name=fields.get('first_name', ''),
            last_name=fields.get('last_name', ''),
            role=fields.get('role', 'jobseeker'),
            plan=fields.get('plan', 'free'),
            country=fields.get('country', 'CI'),
            phone=fields.get('phone', ''),
            is_verified=fields.get('is_verified', False),
            is_active=fields.get('is_active', True),
            is_staff=fields.get('is_staff', False),
            is_superuser=fields.get('is_superuser', False),
            date_joined=fields.get('date_joined'),
            last_login=fields.get('last_login'),
        )
        user.set_password(fields.get('password', ''))
        user.save()

    elif model == 'jobs.job':
        title = fields.get('title')
        if not title or Job.objects.filter(title=title, company=fields.get('company', '')).exists():
            continue
        Job.objects.create(
            pk=pk,
            title=title,
            company=fields.get('company', ''),
            location=fields.get('location', ''),
            description=fields.get('description', ''),
            requirements=fields.get('requirements', ''),
            employment_type=fields.get('employment_type', 'full_time'),
            salary_min=fields.get('salary_min'),
            salary_max=fields.get('salary_max'),
            is_active=fields.get('is_active', True),
            posted_at=fields.get('posted_at'),
            deadline=fields.get('deadline'),
            source=fields.get('source', 'backup'),
            country=fields.get('country', 'CI'),
            category=fields.get('category', 'general'),
            remote=fields.get('remote', False),
            external_url=fields.get('external_url', ''),
        )

    elif model == 'employers.employerprofile':
        user_email = fields.get('user')
        if not user_email:
            continue
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            continue
        if EmployerProfile.objects.filter(user=user).exists():
            continue
        EmployerProfile.objects.create(
            pk=pk,
            user=user,
            company_name=fields.get('company_name', ''),
            company_description=fields.get('company_description', ''),
            website=fields.get('website', ''),
            industry=fields.get('industry', ''),
            company_size=fields.get('company_size', ''),
            location=fields.get('location', ''),
            verified=fields.get('verified', False),
        )

print('users', User.objects.count())
print('jobs', Job.objects.count())
print('employer_profiles', EmployerProfile.objects.count())
