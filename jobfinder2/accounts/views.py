from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import User, UserProfile, Skill, Experience, Education
from .forms import SignupForm, LoginForm, ProfileForm, ExperienceForm, EducationForm


def auth_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    login_form = LoginForm()
    signup_form = SignupForm()
    tab = request.GET.get('tab', 'login')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'login':
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                user = authenticate(request,
                    username=login_form.cleaned_data['email'],
                    password=login_form.cleaned_data['password'])
                if user:
                    login(request, user)
                    messages.success(request, f'Bienvenue, {user.first_name or user.email} !')
                    nxt = request.GET.get('next', '')
                    if user.is_employer:
                        return redirect(nxt or 'employers:dashboard')
                    return redirect(nxt or 'core:dashboard')
                login_form.add_error(None, 'Email ou mot de passe incorrect.')
            tab = 'login'
        elif action == 'signup':
            signup_form = SignupForm(request.POST)
            if signup_form.is_valid():
                user = signup_form.save()
                login(request, user, backend='accounts.backends.EmailBackend')
                messages.success(request, 'Compte créé ! Complétez votre profil.')
                if user.is_employer:
                    return redirect('employers:setup')
                return redirect('core:dashboard')
            tab = 'signup'

    return render(request, 'accounts/auth.html', {
        'login_form': login_form, 'signup_form': signup_form, 'tab': tab,
    })


def logout_view(request):
    logout(request)
    messages.info(request, 'Vous avez été déconnecté.')
    return redirect('core:home')


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    tab = request.GET.get('tab', 'personal')

    if request.method == 'POST':
        section = request.POST.get('section')

        if section == 'personal':
            form = ProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
                request.user.first_name = request.POST.get('first_name', '')
                request.user.last_name  = request.POST.get('last_name', '')
                request.user.save(update_fields=['first_name', 'last_name'])
                profile.compute_completion()
                messages.success(request, 'Profil mis à jour ✓')
            else:
                messages.error(request, 'Erreur dans le formulaire.')
            return redirect('/auth/profile/?tab=personal')

        elif section == 'experience':
            f = ExperienceForm(request.POST)
            if f.is_valid():
                e = f.save(commit=False); e.profile = profile; e.save()
                profile.compute_completion()
                messages.success(request, 'Expérience ajoutée ✓')
            else:
                messages.error(request, 'Erreur formulaire expérience.')
            return redirect('/auth/profile/?tab=experience')

        elif section == 'education':
            f = EducationForm(request.POST)
            if f.is_valid():
                e = f.save(commit=False); e.profile = profile; e.save()
                profile.compute_completion()
                messages.success(request, 'Formation ajoutée ✓')
            else:
                messages.error(request, 'Erreur formulaire formation.')
            return redirect('/auth/profile/?tab=education')

        elif section == 'skill':
            name  = request.POST.get('skill_name', '').strip()
            cat   = request.POST.get('skill_category', 'technical')
            level = request.POST.get('skill_level', '')
            if name:
                skill, created = Skill.objects.get_or_create(
                    profile=profile, name=name,
                    defaults={'category': cat, 'level': level}
                )
                if not created:
                    # Mise à jour de la catégorie et du niveau même si déjà existant
                    Skill.objects.filter(profile=profile, name=name).update(
                        category=cat, level=level
                    )
                    messages.info(request, '"' + name + '" mis à jour ✓')
                else:
                    profile.compute_completion()
                    messages.success(request, '"' + name + '" ajouté ✓')
            else:
                messages.warning(request, 'Nom de compétence vide.')
            return redirect('/auth/profile/?tab=skills')

        elif section == 'cv_upload':
            if 'cv_file' in request.FILES:
                from django.utils import timezone
                import os
                cv = request.FILES['cv_file']
                MAX_SIZE = 5 * 1024 * 1024  # 5 Mo
                if cv.size > MAX_SIZE:
                    messages.error(request, 'Fichier trop volumineux (max 5 Mo).')
                else:
                    allowed_ext = ['.pdf', '.doc', '.docx', '.txt']
                    ext = os.path.splitext(cv.name)[1].lower()
                    if ext not in allowed_ext:
                        messages.error(request, 'Format non accepté. Utilisez PDF, DOC, DOCX ou TXT.')
                    else:
                        profile.cv_file = cv
                        profile.cv_uploaded_at = timezone.now()
                        profile.save(update_fields=['cv_file','cv_uploaded_at'])
                        profile.compute_completion()
                        # Auto-parsing IA du CV
                        try:
                            _auto_parse_cv(request.user, profile)
                            messages.success(request, 'CV uploadé et analysé par l\'IA — profil mis à jour ✓')
                        except Exception:
                            messages.success(request, 'CV uploadé ✓')
            else:
                messages.warning(request, 'Aucun fichier sélectionné.')
            return redirect('/auth/profile/?tab=documents')

    profile.compute_completion()
    return render(request, 'accounts/profile.html', {
        'profile': profile, 'tab': tab,
        'profile_form': ProfileForm(instance=profile, initial={
            'first_name': request.user.first_name,
            'last_name':  request.user.last_name,
        }),
        'exp_form': ExperienceForm(),
        'edu_form': EducationForm(),
        'skills':      profile.skills.all().order_by('category','name'),
        'experiences': profile.experiences.all(),
        'educations':  profile.educations.all(),
    })


@login_required
@require_POST
def delete_skill(request, pk):
    try:
        s = Skill.objects.get(pk=pk, profile__user=request.user)
        s.delete()
        request.user.profile.compute_completion()
        return JsonResponse({'ok': True})
    except Skill.DoesNotExist:
        return JsonResponse({'ok': False}, status=404)


@login_required
@require_POST
def delete_experience(request, pk):
    """Supprimer une expérience"""
    try:
        exp = Experience.objects.get(pk=pk, profile__user=request.user)
        exp.delete()
        request.user.profile.compute_completion()
        return JsonResponse({'ok': True})
    except Experience.DoesNotExist:
        return JsonResponse({'ok': False}, status=404)


@login_required
@require_POST
def delete_education(request, pk):
    """Supprimer une formation"""
    try:
        edu = Education.objects.get(pk=pk, profile__user=request.user)
        edu.delete()
        request.user.profile.compute_completion()
        return JsonResponse({'ok': True})
    except Education.DoesNotExist:
        return JsonResponse({'ok': False}, status=404)


@login_required
def update_experience(request, pk):
    """Modifier une expérience"""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    try:
        exp = Experience.objects.get(pk=pk, profile=profile)
    except Experience.DoesNotExist:
        messages.error(request, 'Expérience non trouvée')
        return redirect('/auth/profile/?tab=experience')
    
    if request.method == 'POST':
        form = ExperienceForm(request.POST, instance=exp)
        if form.is_valid():
            form.save()
            profile.compute_completion()
            messages.success(request, 'Expérience mise à jour ✓')
            return redirect('/auth/profile/?tab=experience')
        else:
            messages.error(request, 'Erreur dans le formulaire.')
    else:
        form = ExperienceForm(instance=exp)
    
    return render(request, 'accounts/edit_experience.html', {'form': form, 'experience': exp})


@login_required
def update_education(request, pk):
    """Modifier une formation"""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    try:
        edu = Education.objects.get(pk=pk, profile=profile)
    except Education.DoesNotExist:
        messages.error(request, 'Formation non trouvée')
        return redirect('/auth/profile/?tab=education')
    
    if request.method == 'POST':
        form = EducationForm(request.POST, instance=edu)
        if form.is_valid():
            form.save()
            profile.compute_completion()
            messages.success(request, 'Formation mise à jour ✓')
            return redirect('/auth/profile/?tab=education')
        else:
            messages.error(request, 'Erreur dans le formulaire.')
    else:
        form = EducationForm(instance=edu)
    
    return render(request, 'accounts/edit_education.html', {'form': form, 'education': edu})


@login_required
@require_POST
def apply_cv_import(request):
    """Applique les données extraites du CV au profil."""
    import json
    from django.utils import timezone
    
    # Ensure JSON response (avoid redirect to login page)
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Non connecté'}, status=401)
    
    try:
        body = request.body
        if not body:
            return JsonResponse({'ok': False, 'error': 'Corps de requête vide'})
        data = json.loads(body)
    except json.JSONDecodeError as e:
        return JsonResponse({'ok': False, 'error': 'JSON invalide: ' + str(e)})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': 'Erreur: ' + str(e)})

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    updated = []

    # Infos personnelles
    if data.get('name'):
        parts = data['name'].split(' ', 1)
        if len(parts) >= 2 and not request.user.first_name:
            request.user.first_name = parts[0]
            request.user.last_name  = parts[1]
            request.user.save(update_fields=['first_name','last_name'])

    # Fill desired_title (always update if present in CV data)
    if data.get('title'):
        profile.desired_title = data['title'][:200]
        if 'title' not in updated: updated.append('desired_title')

    if data.get('location') and not profile.location:
        profile.location = data['location'][:200]
        updated.append('location')

    if data.get('summary') and not profile.summary:
        profile.summary = data['summary'][:1000]
        updated.append('summary')

    if updated:
        profile.save(update_fields=updated)

    # Compétences — toutes catégories
    from accounts.models import Skill

    # Compétences techniques
    for skill_name in (data.get('skills_technical') or data.get('skills') or []):
        if skill_name and len(skill_name.strip()) > 1:
            Skill.objects.get_or_create(
                profile=profile,
                name=skill_name.strip()[:100],
                defaults={'category': 'technical'}
            )

    # Outils
    for skill_name in (data.get('skills_tools') or []):
        if skill_name and len(skill_name.strip()) > 1:
            Skill.objects.get_or_create(
                profile=profile,
                name=skill_name.strip()[:100],
                defaults={'category': 'tool'}
            )

    # Soft skills
    for skill_name in (data.get('skills_soft') or []):
        if skill_name and len(skill_name.strip()) > 1:
            Skill.objects.get_or_create(
                profile=profile,
                name=skill_name.strip()[:100],
                defaults={'category': 'soft'}
            )

    # Certifications
    for skill_name in (data.get('skills_certifications') or []):
        if skill_name and len(skill_name.strip()) > 1:
            Skill.objects.get_or_create(
                profile=profile,
                name=skill_name.strip()[:100],
                defaults={'category': 'technical'}
            )

    # Langues
    for lang in (data.get('languages') or []):
        level_map = {
            'débutant': 'debutant', 'intermédiaire': 'intermediaire',
            'avancé': 'avance', 'bilingue': 'bilingue', 'natif': 'bilingue',
        }
        level = ''
        for k, v in level_map.items():
            if k in (lang.get('level') or '').lower():
                level = v
                break
        if lang.get('name'):
            Skill.objects.get_or_create(
                profile=profile,
                name=lang['name'].strip()[:100],
                defaults={'category': 'language', 'level': level}
            )

    # Expériences
    from accounts.models import Experience
    from datetime import date
    for exp in (data.get('experiences') or []):
        title = (exp.get('title') or '').strip()
        company = (exp.get('company') or '').strip()
        if not title or not company:
            continue
        # Parse dates
        def parse_date(s):
            if not s: return None
            try:
                from datetime import datetime
                for fmt in ['%Y-%m-%d','%Y-%m','%Y']:
                    try: return datetime.strptime(s[:10], fmt).date()
                    except: pass
            except: pass
            return None
        
        start = parse_date(exp.get('start_date')) or date(2020, 1, 1)
        raw_end = exp.get('end_date')
        end   = parse_date(raw_end) if raw_end else None
        # is_current = True seulement si explicitement indiqué ou pas de date de fin fournie
        is_cur = bool(exp.get('is_current')) or (not raw_end)

        if not Experience.objects.filter(profile=profile, title=title, company=company).exists():
            Experience.objects.create(
                profile=profile,
                title=title[:200],
                company=company[:200],
                location=(exp.get('location') or 'Abidjan, CI')[:200],
                start_date=start,
                end_date=end,
                is_current=is_cur,
                description=(exp.get('description') or '')[:1000],
                technologies=(exp.get('technologies') or '')[:500],
            )

    # Formations
    from accounts.models import Education
    for edu in (data.get('educations') or []):
        degree = (edu.get('degree') or '').strip()
        inst   = (edu.get('institution') or '').strip()
        if not degree: continue
        try:
            sy = int(edu.get('start_year') or 2018)
        except (ValueError, TypeError):
            sy = 2018
        try:
            ey_raw = edu.get('end_year')
            ey = int(ey_raw) if ey_raw else None
        except (ValueError, TypeError):
            ey = None
        if not Education.objects.filter(profile=profile, degree=degree, institution=inst).exists():
            Education.objects.create(
                profile=profile,
                degree=degree[:200],
                institution=(inst or 'Non précisé')[:200],
                location=(edu.get('location') or '')[:200],
                start_year=sy,
                end_year=ey,
                gpa=(edu.get('gpa') or '')[:20],
            )

    profile.compute_completion()
    return JsonResponse({'ok': True})


def _auto_parse_cv(user, profile):
    """
    Lit le CV uploadé, l'envoie à Groq pour extraction structurée,
    puis applique les données au profil (skills, expériences, formations).
    Appelé automatiquement après un upload de CV.
    """
    import io, json as json_lib, re as re_mod
    from ai_tools.groq_client import ask_groq

    cv_file = profile.cv_file
    if not cv_file:
        return

    raw = cv_file.read()
    fname = cv_file.name.lower()
    cv_text = ''
    try:
        if fname.endswith('.pdf'):
            from pypdf import PdfReader
            cv_text = '\n'.join(p.extract_text() or '' for p in PdfReader(io.BytesIO(raw)).pages)
        elif fname.endswith('.docx'):
            from docx import Document
            cv_text = '\n'.join(p.text for p in Document(io.BytesIO(raw)).paragraphs if p.text.strip())
        else:
            cv_text = raw.decode('utf-8', errors='ignore')
    except Exception:
        return

    if not cv_text.strip():
        return

    system = (
        'Tu es expert RH africain spécialisé en extraction de données de CV.\n'
        'Analyse le CV et extrais TOUTES les informations en JSON strict.\n'
        'Réponds UNIQUEMENT avec le JSON — aucun texte avant ou après, pas de backticks.\n'
        'Dates au format YYYY-MM-DD (ou YYYY si seule l\'année est disponible).\n'
        'Champs absents = chaîne vide ou tableau vide.'
    )
    prompt = (
        'Extrais ces champs du CV en JSON valide:\n'
        '{"name":"","email":"","phone":"","location":"","title":"","summary":"",'
        '"skills_technical":[],"skills_tools":[],"skills_soft":[],"languages":[],'
        '"experiences":[{"title":"","company":"","location":"","start_date":"","end_date":"","is_current":false,"description":"","technologies":""}],'
        '"educations":[{"degree":"","institution":"","location":"","start_year":0,"end_year":0,"gpa":""}]}\n\n'
        'CV:\n' + cv_text[:4000]
    )

    raw_result = ask_groq(system, prompt, max_tokens=1600, use_smart_model=True, temperature=0.1)
    clean = re_mod.sub(r'```json|```', '', raw_result).strip()
    m = re_mod.search(r'\{.*\}', clean, re_mod.DOTALL)
    if not m:
        return

    try:
        data = json_lib.loads(m.group())
    except Exception:
        return

    # Appliquer les données extraites via apply_cv_import
    from django.test import RequestFactory
    from django.contrib.auth.middleware import AuthenticationMiddleware
    import json as json_mod

    # Appel direct à la logique d'apply (évite de recréer une requête HTTP)
    _apply_cv_data(user, profile, data)


def _apply_cv_data(user, profile, data):
    """Applique un dict extrait du CV au profil utilisateur."""
    from accounts.models import Skill, Experience, Education
    from datetime import datetime

    updated = []
    if data.get('name') and not user.first_name:
        parts = data['name'].split(' ', 1)
        user.first_name = parts[0]
        user.last_name  = parts[1] if len(parts) > 1 else ''
        user.save(update_fields=['first_name', 'last_name'])

    if data.get('title') and not profile.desired_title:
        profile.desired_title = data['title'][:200]
        updated.append('desired_title')
    if data.get('location') and not profile.location:
        profile.location = data['location'][:200]
        updated.append('location')
    if data.get('summary') and not profile.summary:
        profile.summary = data['summary'][:1000]
        updated.append('summary')
    if updated:
        profile.save(update_fields=updated)

    # Skills
    for cat, key in [('technical', 'skills_technical'), ('tool', 'skills_tools'),
                     ('soft', 'skills_soft'), ('technical', 'skills_certifications')]:
        for name in (data.get(key) or []):
            if name and len(name.strip()) > 1:
                Skill.objects.get_or_create(profile=profile, name=name.strip()[:100],
                                            defaults={'category': cat})

    for lang in (data.get('languages') or []):
        if isinstance(lang, dict) and lang.get('name'):
            Skill.objects.get_or_create(profile=profile, name=lang['name'].strip()[:100],
                                        defaults={'category': 'language'})
        elif isinstance(lang, str) and lang.strip():
            Skill.objects.get_or_create(profile=profile, name=lang.strip()[:100],
                                        defaults={'category': 'language'})

    # Expériences
    def _parse_dt(s):
        if not s: return None
        for fmt in ['%Y-%m-%d', '%Y-%m', '%Y']:
            try: return datetime.strptime(str(s)[:10], fmt).date()
            except: pass
        return None

    for exp in (data.get('experiences') or []):
        title   = (exp.get('title') or '').strip()
        company = (exp.get('company') or '').strip()
        if not title or not company:
            continue
        sd = _parse_dt(exp.get('start_date')) or _parse_dt('2020')
        if not Experience.objects.filter(profile=profile, title=title, company=company).exists():
            Experience.objects.create(
                profile=profile, title=title[:200], company=company[:200],
                location=(exp.get('location') or '')[:200],
                start_date=sd,
                end_date=_parse_dt(exp.get('end_date')),
                is_current=bool(exp.get('is_current')),
                description=(exp.get('description') or '')[:2000],
                technologies=(exp.get('technologies') or '')[:500],
            )

    # Formations
    for edu in (data.get('educations') or []):
        degree = (edu.get('degree') or '').strip()
        inst   = (edu.get('institution') or '').strip()
        if not degree:
            continue
        try: sy = int(edu.get('start_year') or 2018)
        except: sy = 2018
        try: ey = int(edu.get('end_year')) if edu.get('end_year') else None
        except: ey = None
        if not Education.objects.filter(profile=profile, degree=degree, institution=inst).exists():
            Education.objects.create(
                profile=profile, degree=degree[:200],
                institution=(inst or 'Non précisé')[:200],
                location=(edu.get('location') or '')[:200],
                start_year=sy, end_year=ey,
                gpa=(edu.get('gpa') or '')[:20],
            )

    profile.compute_completion()
