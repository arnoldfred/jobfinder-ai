import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
import django
django.setup()
from django.test import Client
from django.test.utils import override_settings
from accounts.models import User

with override_settings(ALLOWED_HOSTS=['testserver']):
    c = Client()
    data = {
        'action': 'signup',
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'reproreal3@example.com',
        'role': 'jobseeker',
        'country': 'CI',
        'password1': 'TestPass123!',
        'password2': 'TestPass123!',
    }
    resp = c.post('/auth/login/', data, follow=True)
    print('status', resp.status_code)
    print('redirect_chain', resp.redirect_chain)
    print('context_tab', resp.context.get('tab') if resp.context else None)
    print('signup_errors', resp.context['signup_form'].errors if resp.context and 'signup_form' in resp.context else None)
    print('user_exists', User.objects.filter(email='reproreal3@example.com').exists())
