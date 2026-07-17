from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.db.models import Q, FloatField, Value
from django.db.models import OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
from .models import Job, JobMatch, SavedJob
from applications.models import Application
from jobs.scraper import _is_recent_scraped_offer


def _compute_score(user, job):
    """Calcule et stocke le score NLP."""
    try:
        from jobs.matching import compute_match_score
        result = compute_match_score(user, job)
        score  = result.get('score', 0)
        JobMatch.objects.update_or_create(user=user, job=job, defaults={'score': score})
        return score, result
    except Exception:
        return _simple_score(user, job)


def _simple_score(user, job):
    try:
        p = user.profile
        user_skills = set(s.name.lower() for s in p.skills.all())
        for e in p.experiences.all():
            user_skills |= {t.strip().lower() for t in e.technologies.split(',') if t.strip()}
    except Exception:
        user_skills = set()

    job_skills = [s.strip().lower() for s in job.required_skills.split(',') if s.strip()]
    score = 15
    if job_skills:
        matched = [s for s in job_skills if s in user_skills]
        score  += int(len(matched) / len(job_skills) * 55)
    try:
        desired = user.profile.desired_title.lower()
        if any(w in job.title.lower() for w in desired.split() if len(w) > 3):
            score += 15
        if user.profile.experiences.exists():
            score += 10
        if user.profile.educations.exists():
            score += 5
    except Exception:
        pass
    score = max(5, min(95, score))
    JobMatch.objects.update_or_create(user=user, job=job, defaults={'score': score})
    return score, {}


def _cached_score(user, job):
    try:
        return JobMatch.objects.get(user=user, job=job).score, {}
    except JobMatch.DoesNotExist:
        return _compute_score(user, job)


def _build_match_context(user, job):
    """Calcule le score affiché partout avec la même logique de rendu."""
    # Preferer utiliser le résultat complet de compute_match_score afin
    # que la liste des compétences manquantes / trouvées soit cohérente
    # avec le score affiché.
    try:
        from jobs.matching import compute_match_score, compute_learned_adjustment
        result = compute_match_score(user, job)
        score = result.get('score', 0)
        # Normaliser les détails d'affichage à partir du résultat
        match_details = {
            'skills_matched': result.get('matched_skills', []),
            'skills_missing': result.get('missing_skills', []),
            'total_skills': len(result.get('matched_skills', [])) + len(result.get('missing_skills', [])),
            'exp_match': result.get('details', {}).get('exp', 0),
            'edu_match': bool(result.get('details', {}).get('edu', 0)),
            'details': result.get('details', {}),
        }
        try:
            ml_delta, ml_reasons = compute_learned_adjustment(user, job)
        except Exception:
            ml_delta, ml_reasons = 0, []
    except Exception:
        # En cas d'erreur (ex: sklearn manquant), retomber sur le cache/simple
        score, _ = _cached_score(user, job)
        match_details = _match_details(user, job)
        try:
            from jobs.matching import compute_learned_adjustment
            ml_delta, ml_reasons = compute_learned_adjustment(user, job)
        except Exception:
            ml_delta, ml_reasons = 0, []

    adjusted_score = score + ml_delta if ml_delta != 0 else score
    adjusted_score = max(0, min(97, adjusted_score))

    match_details['ml_delta'] = ml_delta
    match_details['ml_reasons'] = ml_reasons
    match_details['base_score'] = score

    chance_level = 'unknown'
    chance_label = 'Connexion requise'
    chance_color = '#8A7840'
    from jobs.matching import get_match_summary
    summary = get_match_summary(adjusted_score)
    if summary['label'] == 'Excellent match':
        chance_level, chance_label, chance_color = 'excellent', 'Excellent profil', '#1E6B40'
    elif summary['label'] == 'Bon match':
        chance_level, chance_label, chance_color = 'bon', 'Bon profil', '#C9A84C'
    elif summary['label'] == 'Match partiel':
        chance_level, chance_label, chance_color = 'moyen', 'Profil partiel', '#B86010'
    elif summary['label'] == 'Faible match':
        chance_level, chance_label, chance_color = 'faible', 'Profil à renforcer', '#B83230'
    else:
        chance_level, chance_label, chance_color = 'faible', 'Profil à renforcer', '#B83230'

    return {
        'score': adjusted_score,
        'match_details': match_details,
        'chance_level': chance_level,
        'chance_label': chance_label,
        'chance_color': chance_color,
    }


def _match_details(user, job):
    try:
        p = user.profile
        us = set(s.name.lower() for s in p.skills.all())
        for e in p.experiences.all():
            us |= {t.strip().lower() for t in e.technologies.split(',') if t.strip()}

        from jobs.matching import build_job_vector, _extract_skills
        js = [s.strip().lower() for s in job.required_skills.split(',') if s.strip()]
        if not js:
            jv = build_job_vector(job)
            js = list(jv['skills'])
            if not js and jv['text']:
                js = [s.lower() for s in _extract_skills(jv['text'])]

        return {
            'skills_matched': [s for s in js if s in us],
            'skills_missing': [s for s in js if s not in us],
            'total_skills':   len(js),
            'exp_match':      p.experiences.count(),
            'edu_match':      p.educations.exists(),
        }
    except Exception:
        return {'skills_matched':[],'skills_missing':[],'total_skills':0,'exp_match':0,'edu_match':False}


def _finalize_match_context_for_display(match_context):
    """Normalise le contexte de matching pour l’affichage sans ajouter de bonus caché."""
    score = int(match_context.get('score', 0))
    details = dict(match_context.get('match_details', {}) or {})
    details.pop('implicit_bonus', None)
    details['implicit_bonus'] = 0

    return {
        'score': score,
        'match_details': details,
        'chance_level': match_context.get('chance_level', 'unknown'),
        'chance_label': match_context.get('chance_label', 'Connexion requise'),
        'chance_color': match_context.get('chance_color', '#8A7840'),
    }


def job_list(request):
    # Filtre par défaut : pays du candidat ou CI
    user_country = 'CI'
    if request.user.is_authenticated:
        try:
            user_country = request.user.country or 'CI'
        except Exception:
            pass

    cutoff = timezone.now() - timedelta(days=90)
    qs = Job.objects.filter(is_active=True).select_related('scraping_source', 'employer')
    qs = qs.exclude(source_type='scraping', posted_at__lt=cutoff)

    q       = request.GET.get('q', '').strip()
    country = request.GET.get('country', user_country)
    domain  = request.GET.get('domain', '')
    jtype   = request.GET.get('type', '')
    remote  = request.GET.get('remote', '')
    default_sort = 'score' if request.user.is_authenticated and not request.user.is_employer else '-posted_at'
    sort    = request.GET.get('sort') or default_sort
    if sort not in ('score', '-posted_at', 'title', 'company'):
        sort = default_sort
    source  = request.GET.get('source', '')

    if q:
        qs = qs.filter(
            Q(title__icontains=q)|Q(company__icontains=q)|
            Q(required_skills__icontains=q)|Q(description__icontains=q)
        )
    if country:
        qs = qs.filter(Q(country=country) | Q(is_remote=True))
    if domain:  qs = qs.filter(domain=domain)
    if jtype:   qs = qs.filter(job_type=jtype)
    if remote:  qs = qs.filter(is_remote=True)
    if source == 'employer':
        qs = qs.filter(source_type__in=['employer', 'manual'])
    elif source == 'scraping':
        qs = qs.filter(source_type='scraping')

    total = 0
    match_map = {}
    saved_ids = set()

    if request.user.is_authenticated and not request.user.is_employer:
        if sort == 'score':
            all_jobs = list(qs)
            from jobs.matching import compute_display_score
            for job in all_jobs:
                base_score, _ = _cached_score(request.user, job)
                score = compute_display_score(request.user, job, base_score=base_score, refresh_base=True)
                match_map[job.id] = score
            all_jobs.sort(
                key=lambda j: (
                    match_map.get(j.id, 0),
                    j.posted_at or timezone.datetime.min.replace(tzinfo=timezone.utc),
                    j.id,
                ),
                reverse=True,
            )
            total = len(all_jobs)
            paginator = Paginator(all_jobs, getattr(settings, 'JOBS_PER_PAGE', 15))
            page_obj = paginator.get_page(request.GET.get('page', 1))
        else:
            score_subq = JobMatch.objects.filter(
                user=request.user, job=OuterRef('pk')
            ).values('score')[:1]
            qs = qs.annotate(
                cached_score=Coalesce(Subquery(score_subq, output_field=FloatField()), Value(0.0))
            )
            if sort in ('-posted_at', 'title', 'company'):
                qs = qs.order_by(sort)
            else:
                qs = qs.order_by('-posted_at')
            total     = qs.count()
            paginator = Paginator(qs, getattr(settings, 'JOBS_PER_PAGE', 15))
            page_obj  = paginator.get_page(request.GET.get('page', 1))
            ids = [j.id for j in page_obj]
            for job in page_obj:
                match_context = _build_match_context(request.user, job)
                match_map[job.id] = match_context['score']
            saved_ids = set(SavedJob.objects.filter(
                user=request.user, job_id__in=ids).values_list('job_id', flat=True))
    elif sort in ('-posted_at', 'title', 'company'):
        qs = qs.order_by(sort)
        total     = qs.count()
        paginator = Paginator(qs, getattr(settings, 'JOBS_PER_PAGE', 15))
        page_obj  = paginator.get_page(request.GET.get('page', 1))
    else:
        qs = qs.order_by('-posted_at')
        total     = qs.count()
        paginator = Paginator(qs, getattr(settings, 'JOBS_PER_PAGE', 15))
        page_obj  = paginator.get_page(request.GET.get('page', 1))

    if request.user.is_authenticated and not request.user.is_employer:
        ids = [j.id for j in page_obj]
        saved_ids = set(SavedJob.objects.filter(
            user=request.user, job_id__in=ids).values_list('job_id', flat=True))
        if sort != 'score':
            for job in page_obj:
                match_context = _build_match_context(request.user, job)
                match_map[job.id] = match_context['score']

    jobs_data = [{'job':j,'score':match_map.get(j.id,0),'saved':j.id in saved_ids} for j in page_obj]

    existing_countries = list(
        Job.objects.filter(is_active=True).values_list('country', flat=True))
    existing_domains = list(
        Job.objects.filter(is_active=True).values_list('domain', flat=True).distinct())

    return render(request, 'jobs/list.html', {
        'jobs_data':   jobs_data,
        'total':       total,
        'page_obj':    page_obj,
        'countries':   Job.get_country_choices_from_values(existing_countries),
        'domains':     [(d, dict(Job.DOMAINS).get(d,d)) for d in existing_domains if d],
        'types':       Job.TYPES,
        'filters':     {'q':q,'country':country,'domain':domain,'type':jtype,'remote':remote,'sort':sort,'source':source},
        'user_country': user_country,
    })


def _all_job_skills(job):
    """
    Retourne la liste des compétences/critères d'une offre pour affichage.
    Stratégie :
      1. required_skills structurés (champ DB)
      2. Extraction via patterns de compétences connus (tech + soft skills CI)
      3. Métadonnées structurées AEJI (Diplôme, Expérience, Secteur)
      4. Phrases "maîtrise de / connaissance en" dans la description libre
    """
    import re
    from jobs.matching import _extract_skills

    collected = []

    # 1. required_skills structurés
    structured = [s.strip() for s in (job.required_skills or '').split(',') if s.strip()]
    collected.extend(structured)

    # 2. Extraction NLP via patterns de compétences connus
    full_text = ' '.join(filter(None, [job.title, job.description, job.missions, job.requirements]))
    nlp_skills = _extract_skills(full_text)
    collected.extend(nlp_skills)

    # 3. Métadonnées structurées AEJI/scrapées dans la description
    #    Format : "Diplôme requis : INGENIEUR", "Expérience : 2 ANS", etc.
    desc = job.description or ''

    diplome_m = re.search(r'dipl[oô]me\s+requis?\s*:?\s*([^\n]+)', desc, re.I)
    if diplome_m:
        val = diplome_m.group(1).strip()
        if val and val.lower() not in ('aucun', 'aucune', 'non précisé', ''):
            collected.append(f'Diplôme : {val[:60]}')

    exp_m = re.search(r'exp[eé]rience\s*:?\s*([^\n]+)', desc, re.I)
    if exp_m:
        val = exp_m.group(1).strip()
        if val and re.search(r'\d', val):   # Contient un chiffre → "2 ANS", "Minimum 10 ans"
            collected.append(f'Expérience : {val[:60]}')

    niveau_m = re.search(r'niveau\s*:?\s*([^\n]+)', desc, re.I)
    if niveau_m:
        val = niveau_m.group(1).strip()
        if val and 'bac' in val.lower():
            collected.append(val.upper()[:30])

    # Secteur d'activité — retirer le préfixe verbeux
    secteur_m = re.search(r"secteur\s+d['\s]activit[eé]\s*:?\s*([^\n]{4,60})", desc, re.I)
    if secteur_m:
        val = re.sub(r'\s+', ' ', secteur_m.group(1)).strip()
        # Supprimer les mots administratifs
        val = re.sub(r'\b(autre|autresprec|preciser|san[s]?\s+secteur)\b', '', val, flags=re.I).strip()
        if val and len(val) > 3:
            collected.append(f'Secteur : {val[:50]}')

    # 4. Phrases compétences libres : "maîtrise de X", "connaissance en X", "savoir X"
    comp_pattern = re.compile(
        r'(?:ma[îi]trise|connaissance|notions?|pratique|'
        r'capacit[eé]|aptitude|savoir[\s-](?:faire|être)|'
        r'comp[eé]tence)\s+(?:de|du|des|en|sur|avec|d[u\']|d\'une|d[e\']\s+la)?\s*'
        r'([\w\-àâäéèêëîïôùûüÀ-ÿ]+(?:\s+[\w\-àâäéèêëîïôùûüÀ-ÿ]+){0,3})',
        re.I
    )
    _EXCLUDE = {
        'votre','notre','leurs','leur','leur','cette','votre','vous','nous',
        'travail','bonne','bonne','très','avec','sans','dans','pour','plus',
        'même','aussi','bien','tout','tous','avoir','être','faire','aller',
    }
    for m in comp_pattern.finditer(full_text):
        term = m.group(1).strip()
        if len(term) > 3 and term.lower() not in _EXCLUDE:
            collected.append(term.capitalize())

    # Dédupliquer final (insensible à la casse), conserver l'ordre d'importance
    seen = set()
    result = []
    for s in collected:
        key = re.sub(r'\s+', ' ', s).strip().lower()
        if key and key not in seen and len(key) > 2:
            seen.add(key)
            result.append(s.strip())
        if len(result) >= 12:
            break
    return result


def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)
    if job.source_type == 'scraping' and not _is_recent_scraped_offer(job.posted_at):
        raise Http404('Offre trop ancienne')
    job.view_count += 1
    job.save(update_fields=['view_count'])

    score = 0; match_details = {}; profile_data = {}
    is_saved = False; has_applied = False
    chance_level = 'unknown'; chance_label = 'Connexion requise'; chance_color = '#8A7840'
    similar = Job.objects.filter(domain=job.domain, is_active=True).exclude(pk=pk)[:4]

    # Compétences complètes de l'offre (structurées + inférées)
    all_skills = _all_job_skills(job)

    # Pour les candidats authentifiés : comparer avec leur profil
    skills_annotated = []   # [{'name': str, 'have': bool}]

    if request.user.is_authenticated and not request.user.is_employer:
        # ── Enregistrer l'interaction "vue" ──────────────────────────────
        from applications.models import JobInteraction
        JobInteraction.record(request.user, job, 'viewed')

        match_context = _build_match_context(request.user, job)
        display_context = _finalize_match_context_for_display(match_context)
        score = display_context['score']
        match_details = display_context['match_details']
        chance_level = display_context['chance_level']
        chance_label = display_context['chance_label']
        chance_color = display_context['chance_color']
        try:
            p = request.user.profile
            profile_data = {'cv_uploaded': bool(p.cv_file),
                            'experiences': list(p.experiences.values_list('title', flat=True))}
        except Exception:
            profile_data = {'cv_uploaded': False, 'experiences': []}
        is_saved    = SavedJob.objects.filter(user=request.user, job=job).exists()
        has_applied = Application.objects.filter(user=request.user, job=job).exists()

        # Construire le set de compétences du candidat
        try:
            cand_skills = set(s.name.lower() for s in request.user.profile.skills.all())
            for exp in request.user.profile.experiences.all():
                if exp.technologies:
                    cand_skills |= {t.strip().lower() for t in exp.technologies.split(',') if t.strip()}
            cand_text = ' '.join(filter(None, [
                getattr(request.user.profile, 'desired_title', ''),
                getattr(request.user.profile, 'summary', ''),
            ] + [exp.title for exp in request.user.profile.experiences.all()]))
            cand_text = cand_text.lower()
        except Exception:
            cand_skills = set()
            cand_text = ''

        # Niveau d'éducation du candidat (hiérarchie numérique)
        _EDU_RANK = {
            'doctorat': 5, 'phd': 5,
            'master': 4, 'mba': 4, 'ingénieur': 4, 'ingenieur': 4,
            'bac+5': 4, 'bac 5': 4, 'bac5': 4,
            'licence': 3, 'bachelor': 3,
            'bac+3': 3, 'bac 3': 3, 'bac3': 3,
            'bts': 2, 'dut': 2, 'bac+2': 2, 'bac 2': 2, 'bac2': 2,
            'bac': 1, 'bac+1': 1,
        }
        try:
            from jobs.matching import build_candidate_vector
            cand_vec  = build_candidate_vector(request.user)
            cand_edu  = cand_vec.get('edu_level', '').lower()   # 'master', 'licence', etc.
            cand_rank = _EDU_RANK.get(cand_edu, 0)
            cand_exp_years = cand_vec.get('exp_years', 0)
        except Exception:
            cand_rank = 0
            cand_exp_years = 0

        for sk in all_skills:
            sk_l = sk.lower().strip()

            # ── Diplôme / niveau académique ─────────────────────────────
            if sk_l.startswith('diplôme :') or sk_l.startswith('diplome :'):
                req = sk_l.split(':', 1)[1].strip()
                req_rank = max((_EDU_RANK.get(k, 0) for k in _EDU_RANK if k in req), default=0)
                have = cand_rank >= req_rank if req_rank > 0 else (cand_rank > 0)
                skills_annotated.append({'name': sk, 'have': have, 'type': 'edu'})
                continue

            # ── BAC+X notation directe ───────────────────────────────────
            import re as _re
            bac_m = _re.match(r'bac\s*\+?\s*(\d)', sk_l)
            if bac_m:
                req_n = int(bac_m.group(1))
                req_rank = 1 if req_n <= 1 else 2 if req_n <= 2 else 3 if req_n <= 3 else 4
                have = cand_rank >= req_rank
                skills_annotated.append({'name': sk, 'have': have, 'type': 'edu'})
                continue

            # ── Expérience : X ANS ───────────────────────────────────────
            if sk_l.startswith('expérience :') or sk_l.startswith('experience :'):
                nums = _re.findall(r'\d+', sk_l)
                if nums:
                    req_years = int(nums[0])
                    have = cand_exp_years >= req_years
                else:
                    have = cand_exp_years > 0
                skills_annotated.append({'name': sk, 'have': have, 'type': 'exp'})
                continue

            # ── Secteur : affiché en neutre, pas évaluable comme skill ──
            if sk_l.startswith('secteur :'):
                skills_annotated.append({'name': sk, 'have': None, 'type': 'sector'})
                continue

            # ── Compétence normale : matching texte + profil implicite ────
            sk_l = sk.lower()
            have = sk_l in cand_skills or any(
                (sk_l in c or c in sk_l) and len(c) > 4
                for c in cand_skills
            )
            if not have and cand_text:
                # Si le terme est présent dans le titre/summary/expériences, on considère
                # l'aptitude comme implicite plutôt que totalement manquante.
                have = sk_l in cand_text or any(word in cand_text for word in sk_l.split() if len(word) > 3)
                if have:
                    skills_annotated.append({'name': sk, 'have': None, 'type': 'skill', 'status': 'implicit'})
                    continue
            skills_annotated.append({'name': sk, 'have': have, 'type': 'skill', 'status': 'present' if have else 'missing'})

        # Mettre à jour match_details — exclure secteur du comptage
        skills_have     = [s['name'] for s in skills_annotated if s['have'] is True]
        skills_missing  = [s['name'] for s in skills_annotated if s['have'] is False]
        skills_implicit = [s['name'] for s in skills_annotated if s.get('status') == 'implicit']
        match_details['skills_matched']  = skills_have
        match_details['skills_missing']  = skills_missing
        match_details['skills_implicit'] = skills_implicit
        match_details['total_skills']    = len([s for s in skills_annotated if s['have'] is not None])
    else:
        skills_annotated = [{'name': sk, 'have': None} for sk in all_skills]

    return render(request, 'jobs/detail.html', {
        'job': job, 'score': score, 'match_details': match_details,
        'profile_data': profile_data, 'chance_level': chance_level,
        'chance_label': chance_label, 'chance_color': chance_color,
        'is_saved': is_saved, 'has_applied': has_applied,
        'skills': job.skills_list(),           # conservé pour compatibilité
        'skills_annotated': skills_annotated,  # nouveau : liste enrichie avec couleurs
        'similar': similar,
    })


@login_required
@require_POST
def toggle_save(request, pk):
    from applications.models import JobInteraction
    job = get_object_or_404(Job, pk=pk)
    sv, created = SavedJob.objects.get_or_create(user=request.user, job=job)
    if not created:
        sv.delete()
        # Retirer l'interaction "saved"
        JobInteraction.objects.filter(user=request.user, job=job, action='saved').delete()
        return JsonResponse({'saved': False})
    # Enregistrer l'interaction positive
    JobInteraction.record(request.user, job, 'saved')
    return JsonResponse({'saved': True})


@login_required
def saved_jobs(request):
    saves     = SavedJob.objects.filter(user=request.user).select_related('job')
    match_map = {m['job_id']: m['score']
                 for m in JobMatch.objects.filter(user=request.user).values('job_id','score')}
    data = [{'job':s.job,'score':match_map.get(s.job_id,0),'saved_at':s.saved_at} for s in saves]
    # Réinitialiser le badge sauvegardes dès que la page est chargée (côté serveur, fiable)
    request.session['saved_badge_seen_at'] = timezone.now().isoformat()
    request.session.modified = True
    return render(request, 'jobs/saved.html', {'data': data})


@login_required
@require_POST
def mark_saved_seen(request):
    request.session['saved_badge_seen_at'] = timezone.now().isoformat()
    request.session.modified = True
    return JsonResponse({'status': 'ok'})


@login_required
def apply_job(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)

    from applications.models import JobInteraction
    # Offre externe scrapée → rediriger vers le lien source (avec validation)
    if job.external_url and job.source_type == 'scraping':
        from urllib.parse import urlparse
        parsed = urlparse(job.external_url)
        if not parsed.scheme in ('http', 'https') or not parsed.netloc:
            messages.error(request, "Lien externe invalide pour cette offre.")
            return redirect('jobs:detail', pk=job.pk)
        Application.objects.get_or_create(
            user=request.user, job=job,
            defaults={'status': 'sent', 'cover_message': 'Candidature via lien externe',
                      'applied_at': timezone.now()}
        )
        JobInteraction.record(request.user, job, 'applied')
        return redirect(job.external_url)

    if Application.objects.filter(user=request.user, job=job).exists():
        return render(request, 'jobs/apply_already.html', {'job': job})

    if request.method == 'POST':
        Application.objects.create(
            user=request.user, job=job,
            cover_message=request.POST.get('cover_message',''),
            status='sent', applied_at=timezone.now(),
        )
        # ── Signal ML fort : candidature envoyée ─────────────────────────
        JobInteraction.record(request.user, job, 'applied')
        if job.employer:
            from applications.models import Notification
            Notification.send(
                user=job.employer, notif_type='new_app',
                title='Nouvelle candidature',
                message=f'{request.user.get_full_name() or request.user.email} a postulé pour "{job.title}".',
                link=f'/employers/{job.pk}/candidatures/',
            )
        return render(request, 'jobs/apply_success.html', {'job': job})

    return render(request, 'jobs/apply.html', {'job': job})


# ════════════════════════════════════════════════════════════════════════
#  ML — INTERACTION "PAS INTÉRESSÉ"
# ════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def dismiss_job(request, pk):
    """
    Enregistre un signal négatif (dismissed) sur l'offre.
    Le moteur ML en tiendra compte pour réduire les offres similaires.
    """
    from applications.models import JobInteraction
    job = get_object_or_404(Job, pk=pk)
    JobInteraction.record(request.user, job, 'dismissed')
    # Supprimer si l'offre était sauvegardée
    SavedJob.objects.filter(user=request.user, job=job).delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def interest_job(request, pk):
    """
    Enregistre un signal positif (interested) sur l'offre.
    Le moteur ML proposera plus d'offres similaires à cet utilisateur.
    """
    from applications.models import JobInteraction
    job = get_object_or_404(Job, pk=pk)
    # Toggle : si déjà marqué, on retire
    existing = JobInteraction.objects.filter(user=request.user, job=job, action='interested')
    if existing.exists():
        existing.delete()
        return JsonResponse({'ok': True, 'interested': False})
    JobInteraction.record(request.user, job, 'interested')
    # Annuler un éventuel dismissed
    JobInteraction.objects.filter(user=request.user, job=job, action='dismissed').delete()
    return JsonResponse({'ok': True, 'interested': True})


# ════════════════════════════════════════════════════════════════════════
#  ALERTES DE RECHERCHE
# ════════════════════════════════════════════════════════════════════════

@login_required
def search_alerts(request):
    """Liste des alertes du candidat + formulaire de création."""
    from .models import SearchAlert
    if request.method == 'POST':
        label    = request.POST.get('label', '').strip()
        keywords = request.POST.get('keywords', '').strip()
        domain   = request.POST.get('domain', '')
        job_type = request.POST.get('job_type', '')
        country  = request.POST.get('country', '')
        min_score = int(request.POST.get('min_score', 60))
        if label:
            SearchAlert.objects.create(
                user=request.user, label=label, keywords=keywords,
                domain=domain, job_type=job_type, country=country,
                min_score=min_score,
            )
        return redirect('jobs:search_alerts')

    alerts = SearchAlert.objects.filter(user=request.user)
    return render(request, 'jobs/search_alerts.html', {
        'alerts': alerts,
        'domains': Job.DOMAINS,
        'types':   Job.TYPES,
        'countries': Job.get_country_choices(),
    })


@login_required
@require_POST
def delete_search_alert(request, pk):
    from .models import SearchAlert
    alert = get_object_or_404(SearchAlert, pk=pk, user=request.user)
    alert.delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def toggle_search_alert(request, pk):
    from .models import SearchAlert
    alert = get_object_or_404(SearchAlert, pk=pk, user=request.user)
    alert.is_active = not alert.is_active
    alert.save(update_fields=['is_active'])
    return JsonResponse({'ok': True, 'active': alert.is_active})


def run_search_alerts():
    """
    À appeler périodiquement (ex. APScheduler) : parcourt les alertes actives,
    trouve les offres récentes qui correspondent, et notifie les candidats.
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import SearchAlert, Job
    from jobs.matching import compute_match_score
    from applications.models import Notification

    now     = timezone.now()
    cutoff  = now - timedelta(hours=24)   # Offres des dernières 24h

    for alert in SearchAlert.objects.filter(is_active=True).select_related('user'):
        qs = Job.objects.filter(is_active=True, posted_at__gte=cutoff)
        if alert.keywords:
            words = alert.keywords.split()
            for w in words:
                qs = qs.filter(Q(title__icontains=w) | Q(description__icontains=w))
        if alert.domain:
            qs = qs.filter(domain=alert.domain)
        if alert.job_type:
            qs = qs.filter(job_type=alert.job_type)
        if alert.country:
            qs = qs.filter(Q(country=alert.country) | Q(is_remote=True))

        matches = []
        for job in qs[:30]:
            try:
                result = compute_match_score(alert.user, job)
                if result.get('score', 0) >= alert.min_score:
                    matches.append((job, result['score']))
            except Exception:
                pass

        if matches:
            matches.sort(key=lambda x: -x[1])
            top = matches[:3]
            job_lines = '\n'.join(f'• {j.title} — {j.company} ({s}%)' for j, s in top)
            Notification.send(
                user=alert.user,
                notif_type='system',
                title=f'🔔 {len(matches)} nouvelle{"s" if len(matches) > 1 else ""} offre{"s" if len(matches) > 1 else ""} — {alert.label}',
                message=f'{len(matches)} offre(s) correspondent à votre alerte "{alert.label}" :\n{job_lines}',
                link='/jobs/?q=' + alert.keywords.replace(' ', '+'),
            )
            alert.last_sent = now
            alert.save(update_fields=['last_sent'])
