from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django import forms
from .models import EmployerProfile
from jobs.models import Job
from applications.models import Application


# ===== FORMS =====

class EmployerProfileForm(forms.ModelForm):
    class Meta:
        model = EmployerProfile
        fields = ['company_name','company_logo','company_website','company_description',
                  'company_size','industry','location','phone']
        widgets = {
            'company_name':        forms.TextInput(attrs={'class':'form-input','placeholder':'Nom de votre entreprise'}),
            'company_website':     forms.URLInput(attrs={'class':'form-input','placeholder':'https://...'}),
            'company_description': forms.Textarea(attrs={'class':'form-input','rows':4}),
            'company_size':        forms.Select(attrs={'class':'form-input'}),
            'industry':            forms.TextInput(attrs={'class':'form-input','placeholder':'Secteur d\'activité'}),
            'location':            forms.TextInput(attrs={'class':'form-input','placeholder':'Abidjan, CI'}),
            'phone':               forms.TextInput(attrs={'class':'form-input','placeholder':'+225 ...'}),
        }


class JobPostForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'title','location','country','is_remote','job_type','domain',
            'description','missions','requirements','required_skills','nice_to_have',
            'salary_min','salary_max','salary_currency','salary_display_text',
            'company_about','deadline',
        ]
        widgets = {
            'title':               forms.TextInput(attrs={'class':'form-input','placeholder':'Titre du poste (ex: Développeur Python Senior)'}),
            'location':            forms.TextInput(attrs={'class':'form-input','placeholder':'Abidjan, Cocody'}),
            'country':             forms.Select(attrs={'class':'form-input'}),
            'job_type':            forms.Select(attrs={'class':'form-input'}),
            'domain':              forms.Select(attrs={'class':'form-input'}),
            'description':         forms.Textarea(attrs={'class':'form-input','rows':6,'placeholder':'Décrivez le contexte, l\'entreprise et le poste...'}),
            'missions':            forms.Textarea(attrs={'class':'form-input','rows':5,'placeholder':'- Mission 1\n- Mission 2\n- Mission 3'}),
            'requirements':        forms.Textarea(attrs={'class':'form-input','rows':5,'placeholder':'Profil recherché, formation, expérience requise...'}),
            'required_skills':     forms.TextInput(attrs={'class':'form-input','placeholder':'Python, SQL, Excel... (séparés par des virgules)'}),
            'nice_to_have':        forms.Textarea(attrs={'class':'form-input','rows':3}),
            'salary_min':          forms.NumberInput(attrs={'class':'form-input','placeholder':'300000'}),
            'salary_max':          forms.NumberInput(attrs={'class':'form-input','placeholder':'500000'}),
            'salary_currency':     forms.TextInput(attrs={'class':'form-input'}),
            'salary_display_text': forms.TextInput(attrs={'class':'form-input','placeholder':'Ou texte libre: Selon profil, 300K-500K FCFA...'}),
            'company_about':       forms.Textarea(attrs={'class':'form-input','rows':3,'placeholder':'Quelques mots sur votre entreprise pour les candidats...'}),
            'deadline':            forms.DateInput(attrs={'class':'form-input','type':'date'}),
        }
        labels = {
            'title':               'Titre du poste *',
            'location':            'Lieu de travail *',
            'job_type':            'Type de contrat *',
            'domain':              'Domaine *',
            'description':         'Description du poste *',
            'missions':            'Missions principales',
            'requirements':        'Profil recherché',
            'required_skills':     'Compétences requises',
            'nice_to_have':        'Atouts supplémentaires',
            'salary_display_text': 'Affichage salaire (texte libre)',
            'deadline':            'Date limite de candidature',
        }


# ===== VIEWS =====

def employer_required(view_func):
    """Décorateur: réserve la vue aux employeurs."""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/auth/login/?next={request.path}')
        if not request.user.is_employer:
            messages.error(request, 'Accès réservé aux recruteurs.')
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return wrapper


@employer_required
def employer_dashboard(request):
    from django.db.models import Count
    user = request.user
    ep, _ = EmployerProfile.objects.get_or_create(
        user=user, defaults={'company_name': user.get_full_name() or user.email}
    )

    jobs = Job.objects.filter(employer=user).order_by('-posted_at').annotate(
        app_count=Count('applications')
    )
    total_apps  = Application.objects.filter(job__employer=user).count()
    total_views = sum(j.view_count for j in jobs)

    # ── Estimateurs de correspondance candidat/offre ─────────────
    jobs_with_match = []
    for job in jobs:
        apps = Application.objects.filter(job=job).select_related(
            'user', 'user__profile'
        ).order_by('-applied_at')

        candidates_with_score = []
        for app in apps[:20]:
            try:
                from jobs.matching import compute_match_score
                result = compute_match_score(app.user, job)
                match_score  = result.get('score', 0)
                match_label  = result.get('label', '')
                match_color  = result.get('color', 'gray')
                matched_skills = result.get('matched_skills', [])
            except Exception:
                match_score  = 0
                match_label  = 'Non calculé'
                match_color  = 'gray'
                matched_skills = []

            candidates_with_score.append({
                'app':            app,
                'match_score':    match_score,
                'match_label':    match_label,
                'match_color':    match_color,
                'matched_skills': matched_skills[:5],
            })

        candidates_with_score.sort(key=lambda x: -x['match_score'])

        avg_match = 0
        if candidates_with_score:
            avg_match = round(
                sum(c['match_score'] for c in candidates_with_score) / len(candidates_with_score)
            )

        jobs_with_match.append({
            'job':            job,
            'app_count':      job.app_count,
            'avg_match':      avg_match,
            'top_candidates': candidates_with_score[:5],
        })

    # Moyenne globale du matching (uniquement offres avec candidats)
    scored_avgs = [jm['avg_match'] for jm in jobs_with_match if jm['avg_match'] > 0]
    global_avg_match = round(sum(scored_avgs) / len(scored_avgs)) if scored_avgs else 0

    return render(request, 'employers/dashboard.html', {
        'ep':             ep,
        'jobs':           jobs,
        'jobs_with_match': jobs_with_match,
        'global_avg_match': global_avg_match,
        'stats': {
            'total_jobs':  jobs.count(),
            'active_jobs': jobs.filter(is_active=True).count(),
            'total_apps':  total_apps,
            'total_views': total_views,
        },
    })


@employer_required
def job_tracking(request):
    """Affiche le suivi complet des offres avec l'état d'avancement de chaque candidature."""
    user = request.user
    ep, _ = EmployerProfile.objects.get_or_create(user=user, defaults={'company_name': user.get_full_name() or user.email})
    jobs = Job.objects.filter(employer=user).order_by('-posted_at')
    
    # Enrichir chaque offre avec les stats d'avancement
    job_tracking_data = []
    for job in jobs:
        apps = Application.objects.filter(job=job)
        status_breakdown = {
            'sent': apps.filter(status='sent').count(),
            'viewed': apps.filter(status='viewed').count(),
            'pending': apps.filter(status='pending').count(),
            'interview': apps.filter(status='interview').count(),
            'offer': apps.filter(status='offer').count(),
            'accepted': apps.filter(status='accepted').count(),
            'rejected': apps.filter(status='rejected').count(),
            'withdrawn': apps.filter(status='withdrawn').count(),
        }
        
        # Déterminer l'étape majoritaire
        status_list = [s for s in ['accepted', 'offer', 'interview', 'pending', 'viewed', 'sent', 'rejected', 'withdrawn'] 
                      if status_breakdown[s] > 0]
        primary_status = status_list[0] if status_list else 'sent'
        
        job_tracking_data.append({
            'job': job,
            'total_apps': apps.count(),
            'status_breakdown': status_breakdown,
            'primary_status': primary_status,
        })
    
    return render(request, 'employers/job_tracking.html', {
        'ep': ep,
        'job_tracking_data': job_tracking_data,
    })


@employer_required
def employer_setup(request):
    ep, _ = EmployerProfile.objects.get_or_create(user=request.user,
        defaults={'company_name': request.user.get_full_name() or 'Mon Entreprise'})
    if request.method == 'POST':
        form = EmployerProfileForm(request.POST, request.FILES, instance=ep)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil entreprise enregistré ✓')
            return redirect('employers:dashboard')
    else:
        form = EmployerProfileForm(instance=ep)
    return render(request, 'employers/setup.html', {'form': form, 'ep': ep})


@employer_required
def post_job(request, pk=None):
    """Créer ou modifier une offre."""
    job = get_object_or_404(Job, pk=pk, employer=request.user) if pk else None
    ep, _ = EmployerProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = JobPostForm(request.POST, request.FILES, instance=job)
        if form.is_valid():
            j = form.save(commit=False)
            j.employer = request.user
            j.source_type = 'employer'
            j.company = ep.company_name
            if ep.company_logo:
                j.company_logo = ep.company_logo
            j.is_active = True
            is_new = not pk
            j.save()
            action = 'modifiée' if pk else 'publiée'
            messages.success(request, f'Offre {action} avec succès ✓')
            # Notifier les candidats dont les alertes correspondent à cette nouvelle offre
            if is_new:
                try:
                    import threading
                    from jobs.scheduler import _run_search_alerts_check
                    threading.Thread(target=_run_search_alerts_check, args=([j],), daemon=True).start()
                except Exception:
                    pass
            return redirect('employers:dashboard')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = JobPostForm(instance=job)

    return render(request, 'employers/post_job.html', {
        'form': form, 'job': job, 'ep': ep, 'edit': pk is not None,
    })


@employer_required
@require_POST
def toggle_job(request, pk):
    job = get_object_or_404(Job, pk=pk, employer=request.user)
    job.is_active = not job.is_active
    job.save(update_fields=['is_active'])
    return JsonResponse({'active': job.is_active})


@employer_required
def job_applications(request, pk):
    from django.shortcuts import redirect
    return redirect('applications:job_apps', job_pk=pk)


def public_employer(request, pk):
    ep = get_object_or_404(EmployerProfile, pk=pk)
    active_jobs = Job.objects.filter(employer=ep.user, is_active=True).order_by('-posted_at')
    return render(request, 'employers/public.html', {
        'employer': ep.user,
        'profile':  ep,
        'active_jobs': active_jobs,
    })


@employer_required
def view_candidate_profile(request, user_pk):
    """Permet au recruteur de voir le profil complet d'un candidat."""
    from django.contrib.auth import get_user_model
    from applications.models import Application
    User = get_user_model()
    
    candidate = get_object_or_404(User, pk=user_pk, role='jobseeker')
    
    # Vérifier que le recruteur a bien une candidature de ce candidat
    has_application = Application.objects.filter(
        user=candidate, job__employer=request.user
    ).exists()
    
    if not has_application:
        messages.error(request, "Vous n'avez pas accès à ce profil.")
        return redirect('employers:dashboard')
    
    try:
        profile = candidate.profile
    except Exception:
        profile = None
    
    # Candidatures de ce candidat pour les offres du recruteur
    apps = Application.objects.filter(
        user=candidate, job__employer=request.user
    ).select_related('job')
    
    return render(request, 'employers/candidate_profile.html', {
        'candidate': candidate,
        'profile':   profile,
        'skills':    profile.skills.all() if profile else [],
        'experiences': profile.experiences.all() if profile else [],
        'educations':  profile.educations.all() if profile else [],
        'applications': apps,
    })


# ═══════════════════════════════════════════════════════════
#  ESTIMATEUR DE CORRESPONDANCE — candidats vs offres
# ═══════════════════════════════════════════════════════════

@employer_required
def candidate_match_overview(request):
    """
    Pour chaque offre du recruteur, affiche les candidats avec leur score de matching.
    Permet au recruteur de voir instantanément quels candidats correspondent le mieux.
    """
    user = request.user
    ep, _ = EmployerProfile.objects.get_or_create(
        user=user, defaults={'company_name': user.get_full_name() or user.email})
    jobs = Job.objects.filter(employer=user, is_active=True).order_by('-posted_at')

    data = []
    for job in jobs:
        apps = Application.objects.filter(job=job).select_related('user', 'user__profile')
        candidates_with_scores = []
        for app in apps:
            # Calculer ou récupérer le score de matching
            try:
                from jobs.matching import compute_match_score
                from jobs.models import JobMatch
                try:
                    jm = JobMatch.objects.get(user=app.user, job=job)
                    score = jm.score
                except JobMatch.DoesNotExist:
                    result = compute_match_score(app.user, job)
                    score  = result.get('score', 0)
                    JobMatch.objects.create(user=app.user, job=job, score=score)

                # Détails compétences
                try:
                    p = app.user.profile
                    user_skills = set(s.name.lower() for s in p.skills.all())
                    job_skills  = [s.strip().lower() for s in job.required_skills.split(',') if s.strip()]
                    matched = [s for s in job_skills if s in user_skills]
                    missing = [s for s in job_skills if s not in user_skills]
                    exp_count = p.experiences.count()
                    has_cv    = bool(p.cv_file)
                except Exception:
                    matched = missing = []; exp_count = 0; has_cv = False

                # Label couleur du score
                if score >= 80:   score_color, score_label = '#1E6B40', 'Excellent'
                elif score >= 65: score_color, score_label = '#C9A84C', 'Bon profil'
                elif score >= 45: score_color, score_label = '#B86010', 'Partiel'
                else:             score_color, score_label = '#B83230', 'Faible'

                candidates_with_scores.append({
                    'app':          app,
                    'candidate':    app.user,
                    'score':        score,
                    'score_label':  score_label,
                    'score_color':  score_color,
                    'matched':      matched[:5],
                    'missing':      missing[:5],
                    'exp_count':    exp_count,
                    'has_cv':       has_cv,
                })
            except Exception:
                candidates_with_scores.append({
                    'app': app, 'candidate': app.user,
                    'score': 0, 'score_label': 'N/A', 'score_color': '#888',
                    'matched': [], 'missing': [], 'exp_count': 0, 'has_cv': False,
                })

        # Trier par score décroissant
        candidates_with_scores.sort(key=lambda x: -x['score'])
        data.append({
            'job':        job,
            'candidates': candidates_with_scores,
            'total':      len(candidates_with_scores),
            'best_score': candidates_with_scores[0]['score'] if candidates_with_scores else 0,
        })

    return render(request, 'employers/match_overview.html', {
        'ep': ep, 'data': data,
    })


@employer_required
def candidate_match_detail(request, job_pk, candidate_pk):
    """Détail du matching d'un candidat pour une offre spécifique."""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    job       = get_object_or_404(Job, pk=job_pk, employer=request.user)
    candidate = get_object_or_404(User, pk=candidate_pk)

    # Vérifier qu'il y a bien une candidature
    app = get_object_or_404(Application, user=candidate, job=job)

    try:
        from jobs.matching import compute_match_score
        from jobs.models import JobMatch
        try:
            jm    = JobMatch.objects.get(user=candidate, job=job)
            score = jm.score
            result = compute_match_score(candidate, job)
        except JobMatch.DoesNotExist:
            result = compute_match_score(candidate, job)
            score  = result.get('score', 0)
    except Exception:
        result = {}; score = 0

    try:
        profile = candidate.profile
        skills  = profile.skills.all()
        exps    = profile.experiences.all()
        edus    = profile.educations.all()
    except Exception:
        profile = skills = exps = edus = None

    return render(request, 'employers/candidate_match_detail.html', {
        'job': job, 'candidate': candidate, 'app': app,
        'profile': profile, 'skills': skills or [],
        'experiences': exps or [], 'educations': edus or [],
        'score': score, 'match_result': result,
        'details': result.get('details', {}),
        'matched_skills': result.get('matched_skills', []),
        'missing_skills': result.get('missing_skills', []),
    })
