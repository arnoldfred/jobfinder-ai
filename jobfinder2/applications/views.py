import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Application, Notification, Message
from jobs.models import Job


# ─── CANDIDAT : historique ────────────────────────────────
@login_required
def history(request):
    apps = Application.objects.filter(user=request.user).select_related('job', 'job__employer')
    sf   = request.GET.get('status', '')
    if sf:
        apps = apps.filter(status=sf)
    all_apps = Application.objects.filter(user=request.user)
    stats = {
        'total':     all_apps.count(),
        'pending':   all_apps.filter(status__in=['pending', 'interview']).count(),
        'accepted':  all_apps.filter(status='accepted').count(),
        'rejected':  all_apps.filter(status='rejected').count(),
        'interview': all_apps.filter(status='interview').count(),
    }
    # Marquer les notifs de statut comme lues
    Notification.objects.filter(
        user=request.user, notif_type='app_status', is_read=False
    ).update(is_read=True)

    return render(request, 'applications/history.html', {
        'applications': apps,
        'status_filter': sf,
        'stats': stats,
        'choices': Application.STATUS,
    })


# ─── CANDIDAT : détail candidature ───────────────────────
@login_required
def app_detail(request, pk):
    try:
        app = Application.objects.get(pk=pk)
    except Application.DoesNotExist:
        raise Http404("Candidature non trouvée")
    
    # Vérifier les permissions (candidat OU recruteur de l'offre)
    is_candidate = app.user == request.user
    is_recruiter = app.job and app.job.employer == request.user
    
    if not is_candidate and not is_recruiter:
        raise Http404("Accès refusé à cette candidature")
    
    msgs = app.messages.select_related('sender').all()
    # Marquer les messages comme lus
    msgs.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    return render(request, 'applications/detail.html', {
        'app': app, 'messages': msgs, 'is_recruiter': is_recruiter,
    })


# ─── CANDIDAT : postuler ─────────────────────────────────
@login_required
@require_POST
def apply(request, pk):
    job = get_object_or_404(Job, pk=pk)
    try:
        data = json.loads(request.body)
    except Exception:
        data = {}

    app, created = Application.objects.get_or_create(
        user=request.user, job=job,
        defaults={
            'generated_cv':     data.get('cv', ''),
            'generated_letter': data.get('letter', ''),
            'cover_message':    data.get('message', ''),
        }
    )
    if not created:
        return JsonResponse({'ok': False, 'msg': 'Vous avez déjà postulé à cette offre.'})

    # Notifier le recruteur
    if job.employer:
        Notification.send(
            user=job.employer,
            notif_type='new_app',
            title='Nouvelle candidature',
            message='%s a postulé pour "%s".' % (request.user.get_full_name() or request.user.email, job.title),
            link='/employers/%d/candidatures/' % job.pk,
        )

    return JsonResponse({'ok': True, 'msg': 'Candidature envoyée !'})


# ─── CANDIDAT : retirer candidature ──────────────────────
@login_required
@require_POST
def withdraw(request, pk):
    app = get_object_or_404(Application, pk=pk, user=request.user)
    if app.status not in ('accepted', 'rejected'):
        app.status = 'withdrawn'
        app.save(update_fields=['status'])
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False, 'msg': 'Impossible de retirer cette candidature.'})


# ─── RECRUTEUR : voir les candidatures d'une offre ────────
@login_required
def job_applications(request, job_pk):
    job  = get_object_or_404(Job, pk=job_pk, employer=request.user)
    apps = list(Application.objects.filter(job=job).select_related('user', 'user__profile').order_by('-applied_at'))
    # Marquer comme vues
    Application.objects.filter(job=job, status='sent').update(status='viewed', viewed_at=timezone.now())
    stats = {
        'total':     len(apps),
        'new':       sum(1 for a in apps if a.status in ('sent', 'viewed')),
        'interview': sum(1 for a in apps if a.status == 'interview'),
        'offer':     sum(1 for a in apps if a.status == 'offer'),
        'accepted':  sum(1 for a in apps if a.status == 'accepted'),
    }

    # Calculer le score de matching candidat ↔ offre pour chaque postulant
    from jobs.models import JobMatch
    from jobs.matching import compute_match_score
    match_map = {}
    cached = {m.user_id: m.score for m in JobMatch.objects.filter(job=job, user__in=[a.user for a in apps])}
    for app in apps:
        if app.user_id in cached:
            match_map[app.user_id] = cached[app.user_id]
        else:
            try:
                result = compute_match_score(app.user, job)
                s = result.get('score', 0)
                JobMatch.objects.update_or_create(user=app.user, job=job, defaults={'score': s})
                match_map[app.user_id] = s
            except Exception:
                match_map[app.user_id] = 0

    # Trier par score décroissant
    apps.sort(key=lambda a: -match_map.get(a.user_id, 0))

    return render(request, 'applications/recruiter_list.html', {
        'job': job, 'apps': apps, 'stats': stats,
        'choices': Application.STATUS, 'match_map': match_map,
    })


# ─── RECRUTEUR : changer le statut ───────────────────────
@login_required
@require_POST
def update_status(request, pk):
    data      = json.loads(request.body)
    new_status = data.get('status', '')
    note       = data.get('note', '')
    interview_date = data.get('interview_date', '')

    # Trouver la candidature via l'offre du recruteur
    app = get_object_or_404(
        Application, pk=pk, job__employer=request.user
    )

    valid = [s[0] for s in Application.STATUS]
    if new_status not in valid:
        return JsonResponse({'ok': False, 'msg': 'Statut invalide.'})

    old_status = app.status
    app.status = new_status
    if note:
        app.recruiter_note = note
    if interview_date:
        from django.utils.dateparse import parse_datetime
        app.interview_date = parse_datetime(interview_date)
    app.save()

    # Messages de notification selon le statut
    status_messages = {
        'viewed':    ('Votre candidature a été consultée', 'Le recruteur a consulté votre candidature pour "%s".'),
        'pending':   ('Candidature en cours d\'examen', 'Votre candidature pour "%s" est en cours d\'examen.'),
        'interview': ('Entretien planifié !', 'Vous avez été sélectionné(e) pour un entretien — "%s".'),
        'offer':     ('Offre reçue !', 'Vous avez reçu une offre pour le poste "%s". Connectez-vous pour la consulter.'),
        'accepted':  ('Candidature acceptée !', 'Félicitations ! Votre candidature pour "%s" a été acceptée.'),
        'rejected':  ('Candidature non retenue', 'Votre candidature pour "%s" n\'a pas été retenue cette fois. Continuez vos recherches !'),
    }

    if new_status in status_messages and new_status != old_status:
        title_tpl, msg_tpl = status_messages[new_status]
        job_title = app.job.title if app.job else 'ce poste'
        Notification.send(
            user=app.user,
            notif_type='app_status',
            title=title_tpl,
            message=msg_tpl % job_title,
            link='/applications/%d/' % app.pk,
        )

    return JsonResponse({
        'ok':     True,
        'status': new_status,
        'label':  app.get_status_display(),
        'color':  app.status_text_color,
        'bg':     app.status_bg,
        'toast_msg': f"✅ {app.user.get_full_name() or app.user.email} — {new_status.upper()}" if new_status == 'accepted' else None,
    })


@login_required
def get_badge_counts(request):
    """Retourne le nombre de candidatures et notifications non lues (pour mise à jour AJAX)"""
    unread = Notification.objects.filter(user=request.user, is_read=False)
    unread_notifs = unread.count()
    
    if request.user.is_employer:
        app_count = unread.filter(notif_type='new_app').count()
        last_notif = unread.filter(notif_type='new_app').first()
    else:
        app_count = unread.filter(notif_type='app_status').count()
        last_notif = unread.filter(notif_type='app_status').first()
    
    # Envoyer les infos de la dernière notification pour le toast
    last_notif_data = {}
    if last_notif:
        last_notif_data = {
            'title': last_notif.title,
            'message': last_notif.message[:100],
        }
    
    return JsonResponse({
        'app_count': app_count,
        'unread_notifs': unread_notifs,
        'last_notif': last_notif_data,
    })


@login_required
@require_POST
def mark_read(request):
    """Marque toutes les notifications comme lues"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'ok': True})


@login_required
@require_POST
def mark_type_read(request, notif_type):
    """Marque toutes les notifications d'un type spécifique comme lues"""
    Notification.objects.filter(
        user=request.user, notif_type=notif_type, is_read=False
    ).update(is_read=True)
    return JsonResponse({'ok': True})


# ─── MESSAGERIE : envoyer un message ─────────────────────
@login_required
@require_POST
def send_message(request, app_pk):
    data    = json.loads(request.body)
    content = data.get('content', '').strip()
    if not content:
        return JsonResponse({'ok': False, 'msg': 'Message vide.'})

    app = get_object_or_404(Application, pk=app_pk)

    # Vérifier que l'utilisateur est le candidat ou le recruteur
    is_candidate = app.user == request.user
    is_recruiter = app.job and app.job.employer == request.user
    if not is_candidate and not is_recruiter:
        return JsonResponse({'ok': False, 'msg': 'Accès refusé.'}, status=403)

    msg = Message.objects.create(
        application=app,
        sender=request.user,
        content=content,
    )

    # Notifier le destinataire
    recipient = app.job.employer if is_candidate else app.user
    if recipient:
        sender_name = request.user.get_full_name() or request.user.email
        Notification.send(
            user=recipient,
            notif_type='message',
            title='Nouveau message de %s' % sender_name,
            message=content[:100] + ('...' if len(content) > 100 else ''),
            link='/applications/%d/' % app.pk,
        )

    return JsonResponse({
        'ok': True,
        'message': {
            'content':    msg.content,
            'sender':     request.user.get_full_name() or request.user.email,
            'sent_at':    msg.sent_at.strftime('%d/%m/%Y %H:%M'),
            'is_mine':    True,
        }
    })


# ─── NOTIFICATIONS ────────────────────────────────────────
@login_required
def notifications(request):
    notifs = Notification.objects.filter(user=request.user)
    unread_before = notifs.filter(is_read=False).count()
    # Mark all as read when page is opened
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'applications/notifications.html', {
        'notifications': notifs.all()[:50],
        'unread': unread_before,
    })


@login_required
def unread_count(request):
    """Nombre de notifications non lues (endpoint AJAX)."""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count, 'ok': True})
