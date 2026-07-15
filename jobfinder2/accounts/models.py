from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    ROLES = [('jobseeker', 'Chercheur d\'emploi'), ('employer', 'Recruteur'), ('admin', 'Administrateur')]
    PLANS = [('free', 'Gratuit'), ('premium', 'Premium')]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLES, default='jobseeker')
    plan = models.CharField(max_length=20, choices=PLANS, default='free')
    country = models.CharField(max_length=100, default='CI')
    phone = models.CharField(max_length=30, blank=True)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.get_full_name() or self.email

    def get_plan_display(self):
        return dict(self.PLANS).get(self.plan, self.plan)

    @property
    def is_employer(self):
        return self.role == 'employer'

    @property
    def is_jobseeker(self):
        return self.role == 'jobseeker'

    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_staff or self.is_superuser


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    location = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    summary = models.TextField(blank=True)
    desired_title = models.CharField(max_length=200, blank=True)
    cv_file = models.FileField(upload_to='cvs/', blank=True, null=True)
    cv_uploaded_at = models.DateTimeField(null=True, blank=True)
    completion_score = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profil de {self.user}"

    def compute_completion(self):
        checks = [
            bool(self.user.first_name),
            bool(self.user.last_name),
            bool(self.location),
            bool(self.summary),
            bool(self.desired_title),
            bool(self.cv_file),
            bool(self.linkedin_url),
            self.skills.exists(),
            self.experiences.exists(),
            self.educations.exists(),
        ]
        self.completion_score = int(sum(checks) / len(checks) * 100)
        self.save(update_fields=['completion_score'])
        return self.completion_score


class Skill(models.Model):
    CATS   = [('technical','Technique'),('language','Langue'),('soft','Soft skill'),('tool','Outil')]
    LEVELS = [
        ('', 'Niveau non précisé'),
        ('debutant',      'Débutant (A1/A2)'),
        ('intermediaire', 'Intermédiaire (B1/B2)'),
        ('avance',        'Avancé (C1)'),
        ('bilingue',      'Bilingue / Natif (C2)'),
    ]
    profile  = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='skills')
    name     = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATS, default='technical')
    level    = models.CharField(max_length=20, choices=LEVELS, blank=True, default='')

    class Meta:
        unique_together = ('profile', 'name')

    def __str__(self):
        return self.name + (' (' + self.get_level_display() + ')' if self.level else '')


class Experience(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='experiences')
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    technologies = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.title} @ {self.company}"

    @property
    def duration(self):
        from django.utils import timezone
        end = self.end_date or timezone.now().date()
        months = (end.year - self.start_date.year) * 12 + end.month - self.start_date.month
        y, m = divmod(months, 12)
        if y and m:
            return f"{y} an{'s' if y>1 else ''} {m} mois"
        elif y:
            return f"{y} an{'s' if y>1 else ''}"
        return f"{m} mois"


class Education(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='educations')
    degree = models.CharField(max_length=200)
    institution = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    start_year = models.IntegerField()
    end_year = models.IntegerField(null=True, blank=True)
    gpa = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['-start_year']
