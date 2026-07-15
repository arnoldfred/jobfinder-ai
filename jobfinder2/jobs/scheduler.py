"""
Scraping automatique — JobFinder AI
Utilise APScheduler pour lancer le scraping périodiquement
sans intervention manuelle.

Planning :
  - Toutes les 6h  : AEJI + Abidjan.net
  - Toutes les 6h  : cleanup des offres expirées
"""
import logging
import threading

logger = logging.getLogger(__name__)

_scheduler = None
_lock = threading.Lock()


def _run_scraping():
    """Tâche planifiée : scrape AEJI + Abidjan.net puis recalcule les matches."""
    logger.info('[Scheduler] Démarrage scraping automatique')
    try:
        from jobs.scraper import scrape_agenceemploijeunes, scrape_abidjannet
        j1 = scrape_agenceemploijeunes(max_pages=5)
        j2 = scrape_abidjannet(max_pages=5)
        new_count = len(j1) + len(j2)
        logger.info('[Scheduler] Scraping terminé : %d AEJI + %d Abidjan.net', len(j1), len(j2))

        # Recalculer les matches pour tous les candidats actifs sur les nouvelles offres
        if new_count > 0:
            _recompute_matches(j1 + j2)
            # Notifier les candidats dont les alertes correspondent aux nouvelles offres
            _run_search_alerts_check(j1 + j2)

    except Exception as e:
        logger.error('[Scheduler] Erreur scraping : %s', e)


def _recompute_matches(new_jobs):
    """Recalcule les scores de matching pour tous les candidats sur les nouvelles offres."""
    try:
        from django.contrib.auth import get_user_model
        from jobs.matching import compute_match_score
        from jobs.models import JobMatch

        User = get_user_model()
        candidates = list(
            User.objects.filter(role='jobseeker', is_active=True)
                        .select_related('profile')[:200]
        )

        logger.info('[Scheduler] Recalcul matches : %d candidats x %d offres',
                    len(candidates), len(new_jobs))

        for user in candidates:
            for job in new_jobs:
                try:
                    result = compute_match_score(user, job)
                    JobMatch.objects.update_or_create(
                        user=user, job=job,
                        defaults={'score': result['score']}
                    )
                except Exception:
                    pass

        logger.info('[Scheduler] Recalcul matches terminé')
    except Exception as e:
        logger.error('[Scheduler] Erreur recalcul matches : %s', e)


def _run_search_alerts_check(new_jobs):
    """Vérifie les alertes de recherche actives sur les nouvelles offres et notifie."""
    try:
        from jobs.models import SearchAlert
        from jobs.matching import compute_match_score
        from applications.models import Notification
        from django.db.models import Q

        alerts = list(SearchAlert.objects.filter(is_active=True).select_related('user'))
        logger.info('[Scheduler] Vérification alertes : %d alertes x %d nouvelles offres',
                    len(alerts), len(new_jobs))

        for alert in alerts:
            matched = []
            for job in new_jobs:
                # Filtre rapide avant le calcul de score
                if alert.domain and job.domain != alert.domain:
                    continue
                if alert.job_type and job.job_type != alert.job_type:
                    continue
                if alert.country and job.country != alert.country and not job.is_remote:
                    continue
                if alert.keywords:
                    kws = alert.keywords.lower().split()
                    txt = (job.title + ' ' + job.description).lower()
                    if not any(k in txt for k in kws):
                        continue
                try:
                    result = compute_match_score(alert.user, job)
                    if result.get('score', 0) >= alert.min_score:
                        matched.append((job, result['score']))
                except Exception:
                    pass

            if matched:
                matched.sort(key=lambda x: -x[1])
                top = matched[:3]
                lines = '\n'.join(f'• {j.title} — {j.company} ({s}%)' for j, s in top)
                Notification.send(
                    user=alert.user,
                    notif_type='system',
                    title=f'{len(matched)} nouvelle{"s" if len(matched)>1 else ""} offre{"s" if len(matched)>1 else ""} — {alert.label}',
                    message=f'{lines}',
                    link='/jobs/?q=' + alert.keywords.replace(' ', '+') if alert.keywords else '/jobs/',
                )

    except Exception as e:
        logger.error('[Scheduler] Erreur alertes de recherche : %s', e)


def _run_cleanup():
    """Tâche planifiée : désactiver les offres expirées et nettoyer les URLs invalides."""
    logger.info('[Scheduler] Cleanup des offres expirées et URLs invalides')
    try:
        from jobs.scraper import cleanup_expired_jobs
        from cleanup_invalid_urls import cleanup_invalid_urls

        n = cleanup_expired_jobs(days=60)
        cleanup_invalid_urls()
        logger.info('[Scheduler] Cleanup : %d offres désactivées', n)
    except Exception as e:
        logger.error('[Scheduler] Erreur cleanup : %s', e)


def start():
    """Démarre le scheduler (appelé une seule fois depuis AppConfig.ready)."""
    global _scheduler

    with _lock:
        if _scheduler is not None:
            return  # Déjà démarré

        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        from django.conf import settings

        # Utiliser le fuseau horaire du projet
        tz = getattr(settings, 'TIME_ZONE', 'Africa/Abidjan')

        _scheduler = BackgroundScheduler(timezone=tz)

        # Scraping toutes les 6 heures
        _scheduler.add_job(
            _run_scraping,
            trigger=IntervalTrigger(hours=6),
            id='auto_scraping',
            name='Scraping AEJI + Abidjan.net',
            replace_existing=True,
            misfire_grace_time=300,  # 5 min de tolérance
        )

        # Cleanup toutes les 6 heures pour refléter rapidement l’état des offres
        _scheduler.add_job(
            _run_cleanup,
            trigger=IntervalTrigger(hours=6),
            id='auto_cleanup',
            name='Cleanup offres expirées',
            replace_existing=True,
            misfire_grace_time=600,
        )

        _scheduler.start()
        logger.info('[Scheduler] Démarré — scraping toutes les 6h')
