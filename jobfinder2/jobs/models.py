import re
import unicodedata

from django.db import models
from django.utils import timezone


class JobSource(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    region = models.CharField(max_length=100, default='Côte d\'Ivoire')
    is_active = models.BooleanField(default=True)
    jobs_scraped = models.IntegerField(default=0)
    last_sync = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class Job(models.Model):
    TYPES = [
        ('cdi','CDI'),('cdd','CDD'),('stage','Stage'),
        ('freelance','Freelance'),('remote','Remote'),('alternance','Alternance'),
    ]
    DOMAINS = [
        ('it','Informatique & Tech'),('data','Data & IA'),('finance','Finance & Comptabilité'),
        ('marketing','Marketing & Com'),('design','Design & Créatif'),('rh','RH & Recrutement'),
        ('sante','Santé'),('btp','BTP & Génie Civil'),('commerce','Commerce & Ventes'),
        ('juridique','Juridique'),('education','Éducation'),('autre','Autre'),
    ]
    COUNTRIES = [
        ('CI','Côte d\'Ivoire'),('SN','Sénégal'),('NG','Nigeria'),
        ('GH','Ghana'),('CM','Cameroun'),('ML','Mali'),('BF','Burkina Faso'),
        ('REMOTE','Remote / International'),('AUTRE','Autre'),
    ]
    SOURCE_TYPES = [('scraping','Scraping automatique'),('employer','Offre employeur'),('manual','Saisie manuelle')]

    @classmethod
    def normalize_country_code(cls, value):
        if not value:
            return ''
        text = str(value).strip()
        if not text:
            return ''
        normalized = unicodedata.normalize('NFKD', text)
        normalized = ''.join(ch for ch in normalized if not unicodedata.combining(ch))
        normalized = normalized.replace("'", '').replace('-', '').replace(' ', '').lower()
        normalized = re.sub(r'[^a-z0-9]+', '', normalized)
        aliases = {
            'ci': 'CI',
            'cotedivoire': 'CI',
            'ivorycoast': 'CI',
            'cotedivoireivorycoast': 'CI',
            'sn': 'SN',
            'senegal': 'SN',
            'ng': 'NG',
            'nigeria': 'NG',
            'gh': 'GH',
            'ghana': 'GH',
            'cm': 'CM',
            'cameroun': 'CM',
            'cameroon': 'CM',
            'ml': 'ML',
            'mali': 'ML',
            'bf': 'BF',
            'burkinafaso': 'BF',
            'remote': 'REMOTE',
            'international': 'REMOTE',
            'autre': 'AUTRE',
            'other': 'AUTRE',
        }
        return aliases.get(normalized, '')

    @classmethod
    def get_country_label(cls, code):
        country_map = dict(cls.COUNTRIES)
        return country_map.get(code, code)

    @classmethod
    def get_country_choices_from_values(cls, values, include_blank=False, with_flags=False):
        seen_codes = set()
        choices = []
        flag_map = {
            'CI': '🇨🇮 Côte d\'Ivoire',
            'SN': '🇸🇳 Sénégal',
            'NG': '🇳🇬 Nigeria',
            'GH': '🇬🇭 Ghana',
            'CM': '🇨🇲 Cameroun',
            'ML': '🇲🇱 Mali',
            'BF': '🇧🇫 Burkina Faso',
            'REMOTE': '🌍 Remote / International',
            'AUTRE': '🌍 Autre',
        }
        for value in values or []:
            code = cls.normalize_country_code(value)
            if not code or code in seen_codes:
                continue
            seen_codes.add(code)
            label = cls.get_country_label(code)
            choices.append((code, flag_map.get(code, label) if with_flags else label))
        if include_blank:
            choices.insert(0, ('', '--- Pays ---'))
        return choices

    @classmethod
    def get_country_choices(cls, include_blank=False, with_flags=False):
        return cls.get_country_choices_from_values([code for code, _ in cls.COUNTRIES], include_blank=include_blank, with_flags=with_flags)

    # Infos principales
    title = models.CharField(max_length=300, verbose_name='Titre du poste')
    company = models.CharField(max_length=200, verbose_name='Entreprise')
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    company_about = models.TextField(blank=True, verbose_name='À propos de l\'entreprise')
    location = models.CharField(max_length=200, verbose_name='Localisation')
    country = models.CharField(max_length=10, choices=COUNTRIES, default='CI')
    is_remote = models.BooleanField(default=False)
    job_type = models.CharField(max_length=20, choices=TYPES, default='cdi')
    domain = models.CharField(max_length=20, choices=DOMAINS, default='autre')

    # Contenu
    description = models.TextField(verbose_name='Description du poste')
    missions = models.TextField(blank=True, verbose_name='Missions principales')
    requirements = models.TextField(blank=True, verbose_name='Profil recherché')
    required_skills = models.CharField(max_length=1000, blank=True)
    nice_to_have = models.TextField(blank=True, verbose_name='Atouts supplémentaires')

    # Salaire
    salary_min = models.IntegerField(null=True, blank=True)
    salary_max = models.IntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=10, default='FCFA')
    salary_display_text = models.CharField(max_length=200, blank=True)

    # Source
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES, default='scraping')
    scraping_source = models.ForeignKey(JobSource, on_delete=models.SET_NULL, null=True, blank=True)
    employer = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='posted_jobs')
    external_url = models.URLField(blank=True)
    external_id = models.CharField(max_length=300, blank=True, db_index=True)

    # Statut
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)  # vérifiée par admin
    is_featured = models.BooleanField(default=False)
    deadline = models.DateField(null=True, blank=True, verbose_name='Date limite')

    # Méta
    view_count = models.IntegerField(default=0)
    posted_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-posted_at']
        indexes = [
            models.Index(fields=['country','domain','is_active']),
            models.Index(fields=['is_active','posted_at']),
        ]

    def __str__(self):
        return f"{self.title} — {self.company}"

    @property
    def salary_text(self):
        if self.salary_display_text:
            return self.salary_display_text
        if self.salary_min and self.salary_max:
            return f"{self.salary_min:,} – {self.salary_max:,} {self.salary_currency}/mois".replace(',','.')
        elif self.salary_min:
            return f"À partir de {self.salary_min:,} {self.salary_currency}/mois".replace(',','.')
        return "Salaire non précisé"

    @property
    def flag(self):
        return {'CI':'🇨🇮','SN':'🇸🇳','NG':'🇳🇬','GH':'🇬🇭','CM':'🇨🇲','ML':'🇲🇱','BF':'🇧🇫','REMOTE':'🌐'}.get(self.country,'🌍')

    @property
    def domain_icon(self):
        # Returns lucide icon name for use in templates
        return {'it':'monitor','data':'bar-chart-2','finance':'banknote','marketing':'megaphone',
                'design':'palette','rh':'users','sante':'cross','btp':'hammer',
                'commerce':'handshake','juridique':'scale','education':'book-open','autre':'briefcase'}.get(self.domain,'briefcase')

    def skills_list(self):
        return [s.strip() for s in self.required_skills.split(',') if s.strip()]

    @property
    def days_ago(self):
        delta = timezone.now() - self.posted_at
        if delta.days == 0:
            return "Aujourd'hui"
        elif delta.days == 1:
            return "Hier"
        elif delta.days < 7:
            return f"Il y a {delta.days} jours"
        elif delta.days < 30:
            return f"Il y a {delta.days // 7} semaine{'s' if delta.days//7>1 else ''}"
        return f"Il y a {delta.days // 30} mois"


class JobMatch(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='matches')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='matches')
    score = models.IntegerField(default=0)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user','job')
        ordering = ['-score']


class SavedJob(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user','job')


class SearchAlert(models.Model):
    """Alerte de recherche : notifie le candidat quand une offre correspond à ses critères."""
    user       = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='search_alerts')
    label      = models.CharField(max_length=200, verbose_name='Nom de l\'alerte')
    keywords   = models.CharField(max_length=300, blank=True, verbose_name='Mots-clés')
    domain     = models.CharField(max_length=20, blank=True, choices=Job.DOMAINS)
    job_type   = models.CharField(max_length=20, blank=True, choices=Job.TYPES)
    country    = models.CharField(max_length=10, blank=True, choices=Job.COUNTRIES)
    min_score  = models.IntegerField(default=60, verbose_name='Score minimum (%)')
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_sent  = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Alerte "{self.label}" — {self.user.email}'
