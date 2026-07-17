import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
import django
django.setup()
from accounts.forms import SignupForm
from accounts.models import User


data = {
    'action': 'signup',
    'first_name': 'Test',
    'last_name': 'User',
    'email': 'browserflow2@example.com',
    'role': 'jobseeker',
    'password1': 'TestPass123!',
    'password2': 'TestPass123!',
}
form = SignupForm(data)
print('form_valid', form.is_valid())
print('form_errors', form.errors)
if form.is_valid():
    user = form.save(commit=True)
    print('saved', user.pk, user.email, user.country)
print('db_exists', User.objects.filter(email='browserflow2@example.com').exists())
