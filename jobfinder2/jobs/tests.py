import os
import unittest
from datetime import date, timedelta

from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')

from jobs.matching import compute_match_score, compute_display_score, get_match_summary
from jobs.scraper import _normalize_aeji_offer_url, _extract_offer_links_from_html, _abj_parse_detail, _is_recent_scraped_offer
from jobs.views import _finalize_match_context_for_display


class DummyQuerySet(list):
    def values_list(self, *args, **kwargs):
        return list(self)

    def all(self):
        return self

    def exists(self):
        return bool(self)


class DummyProfile:
    def __init__(self, skills=None, experiences=None, educations=None, desired_title='', summary='', location=''):
        self.skills = DummyQuerySet(skills or [])
        self.experiences = DummyQuerySet(experiences or [])
        self.educations = DummyQuerySet(educations or [])
        self.desired_title = desired_title
        self.summary = summary
        self.location = location


class DummyUser:
    def __init__(self, profile, country='CI'):
        self.profile = profile
        self.country = country


class DummyJob:
    def __init__(self, title='', description='', missions='', requirements='', required_skills='', location='', country='CI', is_remote=False, job_type='cdi'):
        self.title = title
        self.description = description
        self.missions = missions
        self.requirements = requirements
        self.required_skills = required_skills
        self.location = location
        self.country = country
        self.is_remote = is_remote
        self.job_type = job_type


class MatchingScoreTests(unittest.TestCase):
    def test_exact_skill_match_uses_45_points_weight(self):
        user = DummyUser(DummyProfile(skills=['Python']))
        job = DummyJob(required_skills='Python')

        result = compute_match_score(user, job)

        self.assertEqual(result['details']['skills'], 45)
        self.assertGreaterEqual(result['score'], 45)

    def test_match_summary_uses_shared_dashboard_thresholds(self):
        self.assertEqual(get_match_summary(80)['label'], 'Excellent match')
        self.assertEqual(get_match_summary(62)['label'], 'Bon match')
        self.assertEqual(get_match_summary(44)['label'], 'Match partiel')
        self.assertEqual(get_match_summary(25)['label'], 'Faible match')

    def test_compute_display_score_matches_base_score_when_no_ml_delta(self):
        user = DummyUser(DummyProfile(skills=['Python']))
        job = DummyJob(required_skills='Python')

        base_result = compute_match_score(user, job)
        base_score = base_result['score']
        display_score = compute_display_score(user, job, base_score=base_score)

        self.assertEqual(display_score, base_score)

    def test_normalize_aeji_offer_url_uses_detail_route(self):
        self.assertEqual(
            _normalize_aeji_offer_url('/site/offres-emploi/PRES-176670-07-2026'),
            'https://agenceemploijeunes.ci/offres-emploi/PRES-176670-07-2026'
        )

    def test_extract_offer_links_from_html_finds_specific_detail_links(self):
        html = '<html><body><a href="/site/offres-emploi/PRES-176670-07-2026">Offre</a><a href="/site/offres-emplois">Liste</a></body></html>'
        self.assertEqual(
            _extract_offer_links_from_html(html, source='aeji'),
            ['https://agenceemploijeunes.ci/offres-emploi/PRES-176670-07-2026']
        )

    def test_normalize_aeji_offer_url_rejects_listing_without_reference(self):
        self.assertEqual(
            _normalize_aeji_offer_url('https://agenceemploijeunes.ci/site/offres-emplois'),
            ''
        )

    def test_finalize_match_context_keeps_score_consistent_when_implicit_skills_exist(self):
        match_context = {
            'score': 74,
            'chance_level': 'bon',
            'chance_label': 'Bon profil',
            'chance_color': '#C9A84C',
            'match_details': {'skills_implicit': ['Python']},
        }
        display_context = _finalize_match_context_for_display(match_context)
        self.assertEqual(display_context['score'], 74)
        self.assertEqual(display_context['match_details']['implicit_bonus'], 0)

    def test_abj_parse_detail_keeps_offer_when_deadline_is_past(self):
        today = date.today().strftime('%d %B %Y')
        html = f'''
        <html><body>
            <h1>Comptable (CDD)</h1>
            <div class="annonce-p-subtitle">Mission du poste</div>
            <div>Publié le {today}</div>
            <div>Date limite de candidature: {date.today().strftime('%d %B %Y')}</div>
        </body></html>
        '''
        result = _abj_parse_detail('https://annonces.abidjan.net/emplois/999/details/comptable', html)
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], 'Comptable')

    def test_recent_scraped_offer_rule_keeps_only_last_three_months(self):
        now = timezone.now()
        self.assertTrue(_is_recent_scraped_offer(now - timedelta(days=30)))
        self.assertTrue(_is_recent_scraped_offer(now - timedelta(days=90)))
        self.assertFalse(_is_recent_scraped_offer(now - timedelta(days=95)))


if __name__ == '__main__':
    unittest.main()
