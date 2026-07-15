from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='accounts.User')
def create_profile(sender, instance, created, **kwargs):
    if created:
        from .models import UserProfile
        UserProfile.objects.get_or_create(user=instance)


def _invalidate_job_matches(user):
    """Supprime les scores JobMatch du candidat pour forcer un recalcul."""
    try:
        from jobs.models import JobMatch
        deleted, _ = JobMatch.objects.filter(user=user).delete()
        if deleted:
            logger.info('JobMatch invalidés pour %s (%d scores supprimés)', user.email, deleted)
    except Exception as e:
        logger.warning('Erreur invalidation JobMatch: %s', e)


@receiver(post_save, sender='accounts.Skill')
def invalidate_on_skill_change(sender, instance, **kwargs):
    _invalidate_job_matches(instance.profile.user)


@receiver(post_save, sender='accounts.Experience')
def invalidate_on_experience_change(sender, instance, **kwargs):
    _invalidate_job_matches(instance.profile.user)


@receiver(post_save, sender='accounts.Education')
def invalidate_on_education_change(sender, instance, **kwargs):
    _invalidate_job_matches(instance.profile.user)


@receiver(post_save, sender='accounts.UserProfile')
def invalidate_on_profile_change(sender, instance, created, update_fields, **kwargs):
    # Invalider seulement si des champs clés du profil ont changé
    # (pas si seulement completion_score ou cv_uploaded_at sont mis à jour)
    key_fields = {'desired_title', 'location', 'summary', 'cv_file'}
    if update_fields is None or key_fields & set(update_fields):
        if not created:
            _invalidate_job_matches(instance.user)
