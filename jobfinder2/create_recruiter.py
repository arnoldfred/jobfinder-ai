import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
import django
django.setup()
from accounts.models import User
from employers.models import EmployerProfile

email = 'recrutestim@gmail.com'
user, created = User.objects.get_or_create(
    email=email,
    defaults={
        'username': email,
        'first_name': 'Test',
        'last_name': 'Recruteur',
        'role': 'employer',
        'country': 'CI',
    }
)
if created:
    user.set_password('Test1234!')
    user.save()

profile, profile_created = EmployerProfile.objects.get_or_create(
    user=user,
    defaults={'company_name': 'Test Recruteur'}
)
print('CREATED', created, 'PROFILE_CREATED', profile_created, 'USER', user.id, user.email, user.role)
