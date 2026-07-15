from jobs.models import SavedJob
from applications.models import Application, Notification
from django.utils import timezone
import datetime


def global_context(request):
    ctx = {
        'saved_count':    0,
        'app_count':      0,   # candidatures avec nouveau statut non lu
        'unread_notifs':  0,
        'user_profile':   None,
    }
    if request.user.is_authenticated:
        unread = Notification.objects.filter(user=request.user, is_read=False)
        ctx['unread_notifs'] = unread.count()

        if request.user.is_employer:
            # Recruteur: nouvelles candidatures reçues
            ctx['app_count'] = unread.filter(notif_type='new_app').count()
        else:
            # Candidat: changements de statut non lus
            ctx['app_count'] = unread.filter(notif_type='app_status').count()
            
            # Compte seulement les jobs sauvegardés APRÈS le dernier passage sur la page
            # Si jamais visité → 0 (pas de "tu as X sauvegardes" dès la connexion)
            saved_badge_seen = request.session.get('saved_badge_seen_at')
            if saved_badge_seen:
                try:
                    seen_dt = datetime.datetime.fromisoformat(saved_badge_seen)
                    ctx['saved_count'] = SavedJob.objects.filter(
                        user=request.user,
                        saved_at__gt=seen_dt
                    ).count()
                except (ValueError, TypeError):
                    ctx['saved_count'] = 0
            else:
                ctx['saved_count'] = 0

        try:
            ctx['user_profile'] = request.user.profile
        except Exception:
            pass
    return ctx
