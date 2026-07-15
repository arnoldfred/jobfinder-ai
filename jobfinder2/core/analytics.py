from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta


def get_candidate_analytics(user):
    from applications.models import Application
    from jobs.models import Job, JobMatch, SavedJob

    apps    = Application.objects.filter(user=user)
    now     = timezone.now()
    last_7  = now - timedelta(days=7)
    last_30 = now - timedelta(days=30)

    # Compteurs par statut
    total       = apps.count()
    viewed      = apps.filter(status='viewed').count()
    pending     = apps.filter(status='pending').count()
    interview   = apps.filter(status='interview').count()
    offer       = apps.filter(status='offer').count()
    accepted    = apps.filter(status='accepted').count()
    rejected    = apps.filter(status='rejected').count()

    responded     = apps.filter(status__in=['viewed','pending','interview','offer','accepted','rejected']).count()
    response_rate = round(responded / max(total, 1) * 100)
    interview_rate= round(interview / max(total, 1) * 100)

    # Funnel (liste pour le template)
    funnel_list = [
        {'label': 'Envoyées',   'count': total,     'pct': 100},
        {'label': 'Vues',       'count': viewed,    'pct': round(viewed    / max(total,1)*100)},
        {'label': 'En attente', 'count': pending,   'pct': round(pending   / max(total,1)*100)},
        {'label': 'Entretien',  'count': interview, 'pct': round(interview / max(total,1)*100)},
        {'label': 'Offre',      'count': offer,     'pct': round(offer     / max(total,1)*100)},
        {'label': 'Acceptée',   'count': accepted,  'pct': round(accepted  / max(total,1)*100)},
    ]

    # Statuts pour donut
    status_counts = {
        'Envoyées': total, 'Vues': viewed, 'En attente': pending,
        'Entretien': interview, 'Offre reçue': offer,
        'Acceptée': accepted, 'Refusée': rejected,
    }

    # Activité 7 derniers jours
    weekly_apps = []
    days_fr = ['Lun','Mar','Mer','Jeu','Ven','Sam','Dim']
    for i in range(6, -1, -1):
        d = now - timedelta(days=i)
        count = apps.filter(applied_at__date=d.date()).count()
        weekly_apps.append({'day': days_fr[d.weekday()], 'count': count, 'date': d.strftime('%d/%m')})

    # Activité hebdomadaire (8 semaines)
    weekly_trend = []
    for i in range(7, -1, -1):
        ws = now - timedelta(weeks=i+1)
        we = now - timedelta(weeks=i)
        weekly_trend.append({
            'week':  'Cette sem.' if i == 0 else 'S-%d' % i,
            'count': apps.filter(applied_at__gte=ws, applied_at__lt=we).count()
        })

    # Domaines candidatures
    domain_stats = []
    for item in apps.values('job__domain').annotate(n=Count('id')).order_by('-n')[:6]:
        if item['job__domain']:
            domain_stats.append({'domain': item['job__domain'], 'count': item['n']})

    # Scores matching
    matches = JobMatch.objects.filter(user=user).select_related('job')
    avg_score = 0
    top_score = 0
    top_score_job = None
    display_scores = []
    try:
        from jobs.matching import compute_display_score
        for m in matches:
            score = compute_display_score(user, m.job, base_score=m.score, refresh_base=True)
            display_scores.append(score)
            if score > top_score:
                top_score = score
                top_score_job = m.job
    except Exception:
        display_scores = [m.score for m in matches]
        if display_scores:
            top_match = matches.order_by('-score').first()
            top_score = top_match.score if top_match else 0
            top_score_job = top_match.job if top_match else None

    if display_scores:
        avg_score = round(sum(display_scores) / len(display_scores))

    # Meilleurs domaines par score moyen
    best_domains = []
    from jobs.models import Job
    domain_scores = matches.values('job__domain').annotate(avg=Avg('score')).order_by('-avg')[:5]
    for ds in domain_scores:
        if ds['job__domain']:
            domain_name = dict(Job.DOMAINS).get(ds['job__domain'], ds['job__domain'])
            best_domains.append({'domain': domain_name, 'score': round(ds['avg'])})

    return {
        # KPIs dashboard
        'total_apps':    total,
        'interviews':    interview,
        'offers':        offer,
        'accepted':      accepted,
        'rejected':      rejected,
        'response_rate': response_rate,
        'interview_rate':interview_rate,
        'avg_score':     avg_score,
        'top_score':     top_score,
        'top_score_job': top_score_job,
        'apps_last_7':   apps.filter(applied_at__gte=last_7).count(),
        'apps_last_30':  apps.filter(applied_at__gte=last_30).count(),
        # Graphiques
        'funnel':        funnel_list,
        'status_counts': status_counts,
        'weekly_apps':   weekly_apps,
        'weekly_trend':  weekly_trend,
        'domain_stats':  domain_stats,
        'best_domains':  best_domains,
        'saved_count':   SavedJob.objects.filter(user=user).count(),
        # Recommandations
        'recommendations': _get_recs(user, total, response_rate),
        # Compat funnel dict
        'funnel_dict': {
            'sent': total, 'viewed': viewed, 'pending': pending,
            'interview': interview, 'offer': offer,
            'accepted': accepted, 'rejected': rejected,
        },
    }


def _get_recs(user, total_apps, response_rate):
    recs = []
    try:
        profile = user.profile
        score   = profile.completion_score
        if score < 70:
            recs.append({'icon': 'user', 'title': 'Complétez votre profil',
                'desc': 'Profil à %d%% — ajoutez expériences et compétences.' % score,
                'url': '/auth/profile/', 'priority': 'high'})
        if not profile.skills.exists():
            recs.append({'icon': 'settings', 'title': 'Ajoutez vos compétences',
                'desc': 'Sans compétences, le matching IA ne peut pas fonctionner.',
                'url': '/auth/profile/?tab=skills', 'priority': 'high'})
        if not profile.cv_file:
            recs.append({'icon': 'file-text', 'title': 'Uploadez votre CV',
                'desc': 'Les recruteurs consultent systématiquement le CV.',
                'url': '/auth/profile/?tab=documents', 'priority': 'high'})
        if total_apps > 5 and response_rate < 10:
            recs.append({'icon': 'bar-chart-2', 'title': 'Taux de réponse faible (%d%%)' % response_rate,
                'desc': 'Personnalisez chaque candidature avec l\'outil Analyser Offre.',
                'url': '/ai/', 'priority': 'medium'})
        if total_apps == 0:
            recs.append({'icon': 'rocket', 'title': 'Lancez-vous !',
                'desc': 'Aucune candidature encore. Consultez les offres recommandées.',
                'url': '/jobs/', 'priority': 'medium'})
    except Exception:
        pass
    return recs


def get_smart_recommendations(user, limit=8):
    from django.db.models import Q as DbQ
    from jobs.models import Job, JobMatch, SavedJob
    from applications.models import Application

    applied_ids = set(Application.objects.filter(user=user).values_list('job_id', flat=True))
    saved_ids   = set(SavedJob.objects.filter(user=user).values_list('job_id', flat=True))
    exclude_ids = applied_ids | saved_ids

    # Pays du candidat
    user_country = getattr(user, 'country', 'CI') or 'CI'

    # Domaines préférés (basé sur les candidatures passées)
    preferred_domains = list(
        Application.objects.filter(user=user)
        .values('job__domain').annotate(n=Count('id'))
        .order_by('-n').values_list('job__domain', flat=True)[:3]
    )

    match_scores = {m['job_id']: m['score']
                    for m in JobMatch.objects.filter(user=user).values('job_id', 'score')}

    base_qs = Job.objects.filter(is_active=True).exclude(id__in=exclude_ids)

    # Prioriser les offres du pays du candidat + remote (80%), puis autres (20%)
    country_jobs = list(base_qs.filter(
        DbQ(country=user_country) | DbQ(is_remote=True)
    ).order_by('-posted_at')[:80])
    other_jobs = list(base_qs.exclude(
        DbQ(country=user_country) | DbQ(is_remote=True)
    ).order_by('-posted_at')[:20])

    results = []
    for job in country_jobs + other_jobs:
        score = match_scores.get(job.id, 0)
        # Boost domaine préféré
        if job.domain in preferred_domains:
            score = min(score + 10, 99)
        # Boost récence (offres < 3 jours)
        if (timezone.now() - job.posted_at).days <= 3:
            score = min(score + 5, 99)
        # Boost même pays
        if job.country == user_country:
            score = min(score + 8, 99)
        elif job.is_remote:
            score = min(score + 4, 99)
        results.append({'job': job, 'score': score})

    results.sort(key=lambda x: -x['score'])
    return results[:limit]


def get_admin_analytics():
    from django.contrib.auth import get_user_model
    from jobs.models import Job
    from applications.models import Application
    from employers.models import EmployerProfile
    User   = get_user_model()
    now    = timezone.now()
    last_7 = now - timedelta(days=7)

    return {
        'users':     {
            'total':     User.objects.count(),
            'jobseekers':User.objects.filter(role='jobseeker').count(),
            'employers': User.objects.filter(role='employer').count(),
            'new_7d':    User.objects.filter(date_joined__gte=last_7).count(),
        },
        'jobs':      {
            'total':   Job.objects.count(),
            'active':  Job.objects.filter(is_active=True).count(),
            'employer':Job.objects.filter(source_type='employer').count(),
            'scraped': Job.objects.filter(source_type='scraping').count(),
            'new_7d':  Job.objects.filter(posted_at__gte=last_7).count(),
        },
        'apps':      {
            'total':      Application.objects.count(),
            'new_7d':     Application.objects.filter(applied_at__gte=last_7).count(),
            'interviews': Application.objects.filter(status='interview').count(),
            'accepted':   Application.objects.filter(status='accepted').count(),
        },
        'employers': {
            'total':    EmployerProfile.objects.count(),
            'verified': EmployerProfile.objects.filter(is_verified=True).count(),
        },
        'top_domains':   list(Job.objects.filter(is_active=True).values('domain').annotate(n=Count('id')).order_by('-n')[:6]),
        'top_companies': list(Job.objects.filter(is_active=True).values('company').annotate(n=Count('id')).order_by('-n')[:5]),
        'weekly_users':  [{'day': (now-timedelta(days=i)).strftime('%d/%m'), 'count': User.objects.filter(date_joined__date=(now-timedelta(days=i)).date()).count()} for i in range(6,-1,-1)],
        'weekly_jobs':   [{'day': (now-timedelta(days=i)).strftime('%d/%m'), 'count': Job.objects.filter(posted_at__date=(now-timedelta(days=i)).date()).count()} for i in range(6,-1,-1)],
        'weekly_apps':   [{'day': (now-timedelta(days=i)).strftime('%d/%m'), 'count': Application.objects.filter(applied_at__date=(now-timedelta(days=i)).date()).count()} for i in range(6,-1,-1)],
    }
