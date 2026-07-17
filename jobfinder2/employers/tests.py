from django.test import TestCase

from accounts.models import User
from employers.models import EmployerProfile
from employers.views import EmployerProfileForm


class EmployerProfilePersistenceTests(TestCase):
    def test_employer_profile_form_saves_to_database(self):
        user = User.objects.create_user(email='recruiter@example.com', username='recruiter@example.com', password='TestPass123!', role='employer')

        form = EmployerProfileForm(
            data={
                'company_name': 'Acme Corp',
                'company_website': 'https://example.com',
                'company_description': 'Company description',
                'company_size': '11-50',
                'industry': 'Tech',
                'location': 'Abidjan',
                'country': 'CI',
                'phone': '+22500000000',
            },
            instance=EmployerProfile.objects.get_or_create(user=user, defaults={'company_name': user.get_full_name() or 'Mon Entreprise'})[0],
        )

        self.assertTrue(form.is_valid(), form.errors)
        profile = form.save()

        self.assertTrue(EmployerProfile.objects.filter(pk=profile.pk).exists())
        self.assertEqual(profile.company_name, 'Acme Corp')
