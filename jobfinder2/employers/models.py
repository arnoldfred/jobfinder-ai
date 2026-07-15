from django.db import models


class EmployerProfile(models.Model):
    """Profil étendu pour les recruteurs/entreprises."""
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='employer_profile')
    company_name = models.CharField(max_length=200)
    company_logo = models.ImageField(upload_to='employer_logos/', blank=True, null=True)
    company_website = models.URLField(blank=True)
    company_description = models.TextField(blank=True)
    company_size = models.CharField(max_length=50, blank=True,
        choices=[('1-10','1–10 employés'),('11-50','11–50'),('51-200','51–200'),('201-500','201–500'),('500+','500+')])
    industry = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=10, default='CI')
    phone = models.CharField(max_length=30, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name or self.user.email

    @property
    def jobs_count(self):
        return self.user.posted_jobs.filter(is_active=True).count()
