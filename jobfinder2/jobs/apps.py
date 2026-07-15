from django.apps import AppConfig


class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'
    verbose_name = "Offres d'emploi"

    def ready(self):
        # Démarrer le scheduler de scraping automatique.
        # En mode runserver avec autoreloader, seule la seconde exécution
        # (RUN_MAIN=true) doit lancer le scheduler.
        import os
        import sys
        run_main = os.environ.get('RUN_MAIN') == 'true'
        is_dev_server = 'runserver' in sys.argv
        is_production_server = (
            'gunicorn' in os.environ
            or 'uwsgi' in os.environ
            or any('gunicorn' in m for m in sys.modules)
            or any('uwsgi' in m for m in sys.modules)
            or 'gunicorn' in sys.argv[0]
        )

        if run_main or is_production_server:
            try:
                from jobs.scheduler import start
                start()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    'Scheduler non démarré : %s', e
                )
