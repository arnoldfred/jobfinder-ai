from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q, Count
from jobs.models import Job, JobMatch
from applications.models import Application


def _freshness_factor(job):
    """
    Coefficient de fraîcheur basé sur l'âge de l'offre.
    Les offres employeurs (source_type='employer') reçoivent toujours 1.0 :
    un recruteur actif sur la plateforme = offre valide indépendamment de la date.
    """
    # Offre postée directement par un recruteur → toujours considérée "fraîche"
    if getattr(job, 'source_type', '') in ('employer', 'manual'):
        return 1.0

    try:
        posted = job.posted_at
        if hasattr(posted, 'date'):
            posted = posted.date()
        days = (timezone.now().date() - posted).days
    except Exception:
        return 0.80

    if days <= 7:   return 1.00
    if days <= 21:  return 0.92
    if days <= 45:  return 0.80
    if days <= 90:  return 0.65
    return 0.50


def _get_top_matches(user, limit=10):
    """
    Retourne les `limit` offres les mieux matchées pour cet utilisateur.

    Sources combinées : offres scrapées + offres postées par recruteurs.

    Règles de classement :
    - Score NLP réel (0-97) calculé par compute_match_score
    - Offres employeurs : seuil abaissé (35 vs 42) + freshness=1.0 constant
      → un recruteur actif sur la plateforme mérite d'être mis en avant
    - Offres scrapées : seuil 42, freshness décroissant avec l'âge
    - Classement final = score brut, avec fraîcheur seulement comme tie-breaker
    - Scores recalculés si > 14 jours (profil évolue)
    - Exclut les offres déjà postulées
    """
    from jobs.matching import compute_match_score, build_candidate_vector
    import datetime

    applied_ids = set(Application.objects.filter(user=user).values_list('job_id', flat=True))

    try:
        cand = build_candidate_vector(user)
        has_profile = bool(cand['skills'] or cand['title'])
    except Exception:
        has_profile = False

    if not has_profile:
        return []

    # Scores existants en base
    existing_matches = {
        m['job_id']: {'score': m['score'], 'updated': m['computed_at']}
        for m in JobMatch.objects.filter(user=user).values('job_id', 'score', 'computed_at')
    }

    # Toutes les offres actives — employeurs EN PREMIER puis 250 offres scrapées récentes
    # + toutes les offres scrapées déjà scorées par le candidat pour ne pas perdre les bons anciens jobs.
    direct_jobs = list(
        Job.objects.filter(is_active=True, source_type__in=['employer', 'manual'])
        .exclude(id__in=applied_ids)
        .order_by('-posted_at')
    )
    recent_scraped_jobs = list(
        Job.objects.filter(is_active=True, source_type='scraping')
        .exclude(id__in=applied_ids)
        .order_by('-posted_at')[:250]
    )

    scored_job_ids = set(existing_matches) - {job.id for job in direct_jobs} - {job.id for job in recent_scraped_jobs}
    old_scored_jobs = list(
        Job.objects.filter(id__in=scored_job_ids, is_active=True)
        .exclude(id__in=applied_ids)
    )

    active_jobs = direct_jobs + recent_scraped_jobs + old_scored_jobs

    stale_threshold = timezone.now() - datetime.timedelta(days=14)

    # Offres à (re)scorer
    to_score = []
    for job in active_jobs:
        m = existing_matches.get(job.id)
        if m is None or (m['updated'] and m['updated'] < stale_threshold):
            to_score.append(job)
        if len(to_score) >= 120:
            break

    scores = dict(existing_matches)

    for job in to_score:
        try:
            result = compute_match_score(user, job)
            s = result['score']
            JobMatch.objects.update_or_create(
                user=user, job=job,
                defaults={'score': s}
            )
            scores[job.id] = {'score': s, 'updated': timezone.now()}
        except Exception:
            scores[job.id] = {'score': 0, 'updated': timezone.now()}

    ranked = []
    for job in active_jobs:
        entry = scores.get(job.id)
        base_score = entry['score'] if entry else 0

        is_employer = job.source_type in ('employer', 'manual')
        score = 0
        try:
            from jobs.matching import compute_display_score
            score = compute_display_score(user, job, base_score=base_score, refresh_base=True)
        except Exception:
            score = base_score

        # Seuil d'affichage :
        # - Offres employeurs : 35 (recruteur actif = vraie intention d'embauche)
        # - Offres scrapées   : 42 (filtrage plus strict car pas de garantie d'activité)
        threshold = 35 if is_employer else 42
        if score < threshold:
            continue

        freshness  = _freshness_factor(job)

        from jobs.matching import get_match_summary
        summary = get_match_summary(score)
        color = summary['color']
        label = summary['label']

        ranked.append({
            'job':         job,
            'score':       score,
            'rank_score':  score + (5 if is_employer else 0),
            'label':       label,
            'color':       color,
            'freshness':   freshness,
            'is_employer': is_employer,
        })

    ranked.sort(key=lambda x: (x['rank_score'], x['freshness'], x['job'].posted_at), reverse=True)
    return ranked[:limit]


def home(request):
    ci_jobs  = Job.objects.filter(is_active=True, country='CI')
    featured = ci_jobs.filter(is_featured=True).order_by('-posted_at')[:6]
    recent   = ci_jobs.order_by('-posted_at')[:8]
    existing = list(ci_jobs.values('domain').annotate(n=Count('id')).order_by('-n').values_list('domain', flat=True))
    domain_map = dict(Job.DOMAINS)
    return render(request, 'core/home.html', {
        'featured':        featured,
        'recent':          recent,
        'total_jobs':      ci_jobs.count(),
        'total_companies': ci_jobs.values('company').distinct().count(),
        'domains':         [(d, domain_map.get(d, d)) for d in existing if d],
    })


@login_required
def dashboard(request):
    user = request.user
    # Admin → dashboard admin dédié (jamais le dashboard candidat)
    if user.is_staff or user.is_superuser or getattr(user, 'role', '') == 'admin':
        return redirect('core:admin_dashboard')
    # Recruteur → dashboard recruteur
    if user.is_employer:
        return redirect('employers:dashboard')

    from core.analytics import get_candidate_analytics
    analytics = get_candidate_analytics(user)

    # ── Top 10 offres les mieux matchées ──────────────────────────────────────
    top_matches = _get_top_matches(user, limit=10)

    profile_score = 0
    try:
        profile_score = user.profile.completion_score
    except Exception:
        pass

    apps = Application.objects.filter(user=user).select_related('job')
    ai_shortcuts = [
        ('file-text', 'Analyser mon CV',    '/ai/'),
        ('mic',       'Coach entretien',    '/ai/'),
        ('banknote',  'Conseil salaire',    '/ai/'),
        ('search',    'Analyser une offre', '/ai/'),
        ('mail',      'Rédiger un email',   '/ai/'),
    ]
    return render(request, 'core/dashboard.html', {
        'top_matches':   top_matches,
        'analytics':     analytics,
        'profile_score': profile_score,
        'recent_apps':   apps[:5],
        'ai_shortcuts':  ai_shortcuts,
        'stats': {
            'apps_total':    analytics['total_apps'],
            'interviews':    analytics['interviews'],
            'response_rate': analytics['response_rate'],
            'avg_score':     analytics['avg_score'],
            'top_score':     top_matches[0]['score'] if top_matches else analytics['top_score'],
            'top_score_job': top_matches[0]['job'] if top_matches else analytics['top_score_job'],
        },
    })


@login_required
def analytics_page(request):
    from core.analytics import get_candidate_analytics
    return render(request, 'core/analytics.html',
                  {'analytics': get_candidate_analytics(request.user)})


# ════════════════════════════════════════════════════════════════════════════
#  ESPACE ADMINISTRATEUR
# ════════════════════════════════════════════════════════════════════════════

def _admin_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            from django.http import Http404
            raise Http404
        return view_func(request, *args, **kwargs)
    return wrapper


@_admin_required
def admin_dashboard(request):
    """Dashboard admin : KPIs globaux, graphiques, accès rapides."""
    from core.analytics import get_admin_analytics
    analytics = get_admin_analytics()

    # Offres récentes à modérer
    to_verify = Job.objects.filter(
        is_active=True, is_verified=False, source_type='employer'
    ).order_by('-posted_at')[:5]

    # Candidatures récentes
    recent_apps = Application.objects.select_related('user', 'job').order_by('-applied_at')[:8]

    # Utilisateurs récents
    from django.contrib.auth import get_user_model
    User = get_user_model()
    recent_users = User.objects.order_by('-date_joined')[:6]

    return render(request, 'core/admin_dashboard.html', {
        'analytics':    analytics,
        'to_verify':    to_verify,
        'recent_apps':  recent_apps,
        'recent_users': recent_users,
    })


@_admin_required
def admin_users(request):
    """Gestion des utilisateurs — liste, filtres, activation."""
    from django.contrib.auth import get_user_model
    from django.core.paginator import Paginator
    User = get_user_model()

    q    = request.GET.get('q', '').strip()
    role = request.GET.get('role', '')
    plan = request.GET.get('plan', '')

    users = User.objects.select_related('profile').order_by('-date_joined')
    if q:
        users = users.filter(
            Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )
    if role: users = users.filter(role=role)
    if plan: users = users.filter(plan=plan)

    today     = timezone.now().date()
    total     = User.objects.count()
    active    = User.objects.filter(is_active=True).count()
    staff     = User.objects.filter(is_staff=True).count()
    new_today = User.objects.filter(date_joined__date=today).count()

    paginator = Paginator(users, 30)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'core/admin_users.html', {
        'users': page_obj, 'q': q, 'role': role, 'plan': plan,
        'stats': {'total': total, 'active': active, 'staff': staff, 'new_today': new_today},
        'roles': [('', 'Tous'), ('jobseeker', 'Candidats'), ('employer', 'Recruteurs'), ('admin', 'Admins')],
        'plans': [('', 'Tous'), ('free', 'Gratuit'), ('premium', 'Premium')],
    })


@_admin_required
def admin_jobs(request):
    """Gestion des offres — modération, vérification, mise en avant."""
    from django.core.paginator import Paginator
    q      = request.GET.get('q', '').strip()
    status = request.GET.get('status', 'active')
    source = request.GET.get('source', '')
    domain = request.GET.get('domain', '')

    jobs = Job.objects.select_related('employer', 'scraping_source').order_by('-posted_at')
    if q: jobs = jobs.filter(Q(title__icontains=q) | Q(company__icontains=q))
    if status == 'active':      jobs = jobs.filter(is_active=True)
    elif status == 'inactive':  jobs = jobs.filter(is_active=False)
    elif status == 'unverified': jobs = jobs.filter(is_active=True, is_verified=False)
    elif status == 'featured':  jobs = jobs.filter(is_featured=True)
    if source: jobs = jobs.filter(source_type=source)
    if domain: jobs = jobs.filter(domain=domain)

    total_active   = Job.objects.filter(is_active=True).count()
    total_inactive = Job.objects.filter(is_active=False).count()
    total_unverif  = Job.objects.filter(is_active=True, is_verified=False).count()
    total_featured = Job.objects.filter(is_featured=True).count()
    total_employer = Job.objects.filter(source_type='employer').count()
    total_scraped  = Job.objects.filter(source_type='scraping').count()
    total_all      = Job.objects.count()

    paginator = Paginator(jobs, 30)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'core/admin_jobs.html', {
        'page_obj': page_obj,
        'filters': {'q': q, 'status': status, 'source': source, 'domain': domain},
        'stats': {
            'total':      total_all,
            'active':     total_active,
            'inactive':   total_inactive,
            'unverified': total_unverif,
            'featured':   total_featured,
            'employer':   total_employer,
            'scraped':    total_scraped,
        },
        'domains': Job.DOMAINS,
        'sources': Job.SOURCE_TYPES,
    })


@_admin_required
def admin_applications(request):
    """Vue admin de toutes les candidatures avec filtres."""
    from django.core.paginator import Paginator
    q      = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')

    apps = Application.objects.select_related('user', 'job', 'job__employer').order_by('-applied_at')
    if q:
        apps = apps.filter(
            Q(user__email__icontains=q) | Q(job__title__icontains=q) |
            Q(job__company__icontains=q)
        )
    if status:
        apps = apps.filter(status=status)

    total       = Application.objects.count()
    interviews  = Application.objects.filter(status='interview').count()
    accepted    = Application.objects.filter(status='accepted').count()
    today       = timezone.now().date()
    new_today   = Application.objects.filter(applied_at__date=today).count()

    paginator = Paginator(apps, 30)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'core/admin_applications.html', {
        'apps': page_obj, 'q': q, 'status': status,
        'stats': {
            'total': total, 'interviews': interviews,
            'accepted': accepted, 'new_today': new_today,
        },
        'statuses': Application.STATUS,
    })


@_admin_required
def admin_scraping(request):
    """Tableau de bord du scraping — sources, lancer un scraping."""
    from jobs.models import JobSource
    sources = JobSource.objects.all().order_by('-last_sync')
    msg = None

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'scrape_aeji':
            try:
                from jobs.scraper import scrape_agenceemploijeunes
                jobs = scrape_agenceemploijeunes(max_pages=5)
                msg  = ('success', f'{len(jobs)} nouvelles offres AEJI importées.')
            except Exception as e:
                msg = ('error', f'Erreur AEJI: {e}')
        elif action == 'scrape_linkedin':
            try:
                from jobs.scraper import scrape_linkedin_ci
                jobs = scrape_linkedin_ci(max_results=20)
                msg  = ('success', f'{len(jobs)} nouvelles offres LinkedIn importées.')
            except Exception as e:
                msg = ('error', f'Erreur LinkedIn: {e}')
        elif action == 'scrape_abidjannet':
            try:
                from jobs.scraper import scrape_abidjannet
                jobs = scrape_abidjannet(max_pages=5)
                msg  = ('success', f'{len(jobs)} nouvelles offres Abidjan.net importées.')
            except Exception as e:
                msg = ('error', f'Erreur Abidjan.net: {e}')
        elif action == 'scrape_all':
            try:
                from jobs.scraper import scrape_agenceemploijeunes, scrape_abidjannet, scrape_linkedin_ci
                j1 = scrape_agenceemploijeunes(max_pages=5)
                j2 = scrape_abidjannet(max_pages=5)
                j3 = scrape_linkedin_ci(max_results=20)
                msg = ('success', f'{len(j1)} offres AEJI + {len(j2)} offres Abidjan.net + {len(j3)} offres LinkedIn importées.')
            except Exception as e:
                msg = ('error', f'Erreur scraping: {e}')
        elif action == 'cleanup':
            try:
                from jobs.scraper import cleanup_expired_jobs
                n   = cleanup_expired_jobs(days=60)
                msg = ('success', f'{n} offres expirées désactivées.')
            except Exception as e:
                msg = ('error', f'Erreur cleanup: {e}')
        sources = JobSource.objects.all().order_by('-last_sync')

    source_stats = []
    for s in sources:
        active  = Job.objects.filter(scraping_source=s, is_active=True).count()
        total_s = Job.objects.filter(scraping_source=s).count()
        source_stats.append({'source': s, 'active': active, 'total': total_s})

    total_scraped  = Job.objects.filter(source_type='scraping', is_active=True).count()
    total_employer = Job.objects.filter(source_type='employer', is_active=True).count()

    # Statut du scheduler automatique
    scheduler_jobs = []
    try:
        from jobs.scheduler import _scheduler
        if _scheduler and _scheduler.running:
            for job in _scheduler.get_jobs():
                scheduler_jobs.append({
                    'name':     job.name,
                    'next_run': job.next_run_time,
                })
    except Exception:
        pass

    return render(request, 'core/admin_scraping.html', {
        'source_stats':   source_stats,
        'total_scraped':  total_scraped,
        'total_employer': total_employer,
        'scheduler_jobs': scheduler_jobs,
        'msg': msg,
    })


@_admin_required
@require_POST
def admin_toggle_user(request, pk):
    from django.contrib.auth import get_user_model
    user = get_object_or_404(get_user_model(), pk=pk)
    if user.pk == request.user.pk:
        return JsonResponse({'ok': False, 'msg': 'Impossible de vous désactiver vous-même.'})
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    return JsonResponse({'ok': True, 'active': user.is_active})


@_admin_required
@require_POST
def admin_toggle_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    job.is_active = not job.is_active
    job.save(update_fields=['is_active'])
    return JsonResponse({'ok': True, 'active': job.is_active})


@_admin_required
@require_POST
def admin_feature_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    job.is_featured = not job.is_featured
    job.save(update_fields=['is_featured'])
    return JsonResponse({'ok': True, 'featured': job.is_featured})


@_admin_required
@require_POST
def admin_verify_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    job.is_verified = not job.is_verified
    job.save(update_fields=['is_verified'])
    return JsonResponse({'ok': True, 'verified': job.is_verified})


@_admin_required
@require_POST
def admin_promote_user(request, pk):
    """Passer un utilisateur en premium."""
    from django.contrib.auth import get_user_model
    user = get_object_or_404(get_user_model(), pk=pk)
    user.plan = 'premium' if user.plan == 'free' else 'free'
    user.save(update_fields=['plan'])
    return JsonResponse({'ok': True, 'plan': user.plan})


@_admin_required
@require_POST
def admin_delete_job(request, pk):
    """Supprime une offre (admin seulement)."""
    job = get_object_or_404(Job, pk=pk)
    title = job.title
    job.delete()
    return JsonResponse({'ok': True, 'msg': f'Offre "{title}" supprimée.'})


def error_404(request, exception=None):
    return render(request, '404.html', status=404)

def error_500(request):
    return render(request, '500.html', status=500)
