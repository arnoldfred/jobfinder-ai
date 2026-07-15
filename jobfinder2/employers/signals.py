from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='accounts.User')
def create_employer_profile(sender, instance, created, **kwargs):
    if created and instance.role == 'employer':
        from employers.models import EmployerProfile
        EmployerProfile.objects.get_or_create(
            user=instance,
            defaults={'company_name': instance.get_full_name() or instance.email}
        )
