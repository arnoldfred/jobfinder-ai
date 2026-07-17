from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.forms import SignupForm
from accounts.models import User, UserProfile
from employers.models import EmployerProfile
from accounts.views import _extract_professional_summary


class CVExtractionTests(TestCase):
    def test_extract_professional_summary_from_cv_text(self):
        cv_text = """
        RÉSUMÉ PROFESSIONNEL
        Développeur backend Python spécialisé dans les APIs fiables, l'automatisation
        et la livraison de solutions cloud pour des équipes produit.

        EXPÉRIENCES
        - Développeur backend chez CinetTech
        """

        summary = _extract_professional_summary(cv_text)

        self.assertIn('Développeur backend Python', summary)
        self.assertIn('APIs fiables', summary)

    def test_avatar_upload_keeps_existing_profile_fields(self):
        user = User.objects.create_user(
            username='avataruser@example.com',
            email='avataruser@example.com',
            password='TestPass123!',
            first_name='Ada',
            last_name='Lovelace',
        )
        profile = user.profile
        profile.location = 'Abidjan, CI'
        profile.summary = 'Développeuse backend expérimentée.'
        profile.desired_title = 'Développeuse Python'
        profile.save()

        avatar = SimpleUploadedFile('avatar.png', b'fake-image-content', content_type='image/png')
        self.client.force_login(user)
        response = self.client.post(reverse('accounts:profile'), {
            'section': 'personal',
        }, follow=True, format=None, files={'avatar': avatar})

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertEqual(profile.location, 'Abidjan, CI')
        self.assertEqual(profile.summary, 'Développeuse backend expérimentée.')
        self.assertEqual(profile.desired_title, 'Développeuse Python')


class SignupPersistenceTests(TestCase):
    def test_signup_form_persists_user_and_employer_profile(self):
        data = {
            'first_name': 'Test',
            'last_name': 'Form',
            'email': 'regression@example.com',
            'role': 'employer',
            'country': 'CI',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }

        form = SignupForm(data)
        self.assertTrue(form.is_valid(), form.errors)

        user = form.save(commit=True)

        self.assertTrue(User.objects.filter(pk=user.pk).exists())
        self.assertEqual(user.email, 'regression@example.com')
        self.assertEqual(user.role, 'employer')
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertTrue(EmployerProfile.objects.filter(user=user).exists())

    def test_signup_form_defaults_country_to_ci_when_not_selected(self):
        data = {
            'first_name': 'Default',
            'last_name': 'Country',
            'email': 'defaultcountry@example.com',
            'role': 'jobseeker',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }

        form = SignupForm(data)
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save(commit=True)

        self.assertEqual(user.country, 'CI')

    def test_auth_view_persists_user_when_signup_post_uses_signup_fields_without_action_flag(self):
        response = self.client.post(reverse('accounts:auth') + '?tab=signup', {
            'first_name': 'No',
            'last_name': 'Action',
            'email': 'noaction@example.com',
            'role': 'jobseeker',
            'country': 'CI',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='noaction@example.com').exists())
