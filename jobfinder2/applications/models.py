from django.db import models
from django.utils import timezone


class Application(models.Model):
    STATUS = [
        ('sent',       'Envoyée'),
        ('viewed',     'Vue'),
        ('pending',    'En attente'),
        ('interview',  'Entretien'),
        ('offer',      'Offre reçue'),
        ('accepted',   'Acceptée'),
        ('rejected',   'Refusée'),
        ('withdrawn',  'Retirée'),
    ]
    user            = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='applications')
    job             = models.ForeignKey('jobs.Job', on_delete=models.SET_NULL, null=True, related_name='applications')
    generated_cv    = models.TextField(blank=True)
    generated_letter= models.TextField(blank=True)
    status          = models.CharField(max_length=20, choices=STATUS, default='sent')
    cover_message   = models.TextField(blank=True, verbose_name='Message de candidature')
    applied_at      = models.DateTimeField(default=timezone.now)
    updated_at      = models.DateTimeField(auto_now=True)
    interview_date  = models.DateTimeField(null=True, blank=True)
    recruiter_note  = models.TextField(blank=True, verbose_name='Note interne recruteur')
    viewed_at       = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-applied_at']
        unique_together = ('user', 'job')

    def __str__(self):
        return '%s → %s' % (self.user, self.job)

    @property
    def status_color(self):
        return {
            'sent':'blue','viewed':'blue','pending':'orange',
            'interview':'gold','offer':'green','accepted':'green',
            'rejected':'red','withdrawn':'gray',
        }.get(self.status, 'gray')

    @property
    def status_icon(self):
        return {
            'sent':'send','viewed':'eye','pending':'clock',
            'interview':'mic','offer':'gift','accepted':'check-circle',
            'rejected':'x-circle','withdrawn':'minus-circle',
        }.get(self.status, 'file-text')

    @property
    def status_bg(self):
        return {
            'sent':'var(--blue-bg)','viewed':'var(--blue-bg)',
            'pending':'var(--orange-bg)','interview':'var(--gold-bg)',
            'offer':'var(--green-bg)','accepted':'var(--green-bg)',
            'rejected':'var(--red-bg)','withdrawn':'rgba(0,0,0,0.05)',
        }.get(self.status, 'rgba(0,0,0,0.05)')

    @property
    def status_text_color(self):
        return {
            'sent':'var(--blue)','viewed':'var(--blue)',
            'pending':'var(--orange)','interview':'var(--gold-dark)',
            'offer':'var(--green)','accepted':'var(--green)',
            'rejected':'var(--red)','withdrawn':'var(--text-3)',
        }.get(self.status, 'var(--text-3)')


class Notification(models.Model):
    TYPES = [
        ('app_status',   'Statut candidature'),
        ('new_app',      'Nouvelle candidature'),
        ('interview',    'Entretien planifié'),
        ('message',      'Nouveau message'),
        ('system',       'Système'),
    ]
    user       = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    notif_type = models.CharField(max_length=20, choices=TYPES, default='system')
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    link       = models.CharField(max_length=300, blank=True)
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return '%s — %s' % (self.user, self.title)

    @classmethod
    def send(cls, user, notif_type, title, message, link=''):
        return cls.objects.create(
            user=user, notif_type=notif_type,
            title=title, message=message, link=link
        )


class JobInteraction(models.Model):
    """
    Enregistre chaque interaction candidat ↔ offre.
    Utilisé par le moteur ML pour apprendre les préférences utilisateur.

    Poids des actions :
      applied   +3  (signal le plus fort — l'utilisateur a vraiment postulé)
      saved     +2  (intérêt sérieux)
      viewed    +1  (curiosité)
      dismissed -2  (signal négatif — pas intéressé)
    """
    ACTION_CHOICES = [
        ('viewed',     'Vue'),
        ('saved',      'Sauvegardée'),
        ('applied',    'Candidature envoyée'),
        ('interested', 'Ça m\'intéresse'),
        ('dismissed',  'Pas intéressé'),
    ]
    ACTION_WEIGHTS = {'applied': 3, 'saved': 2, 'interested': 2, 'viewed': 1, 'dismissed': -2}

    user       = models.ForeignKey('accounts.User', on_delete=models.CASCADE,
                                   related_name='job_interactions')
    job        = models.ForeignKey('jobs.Job', on_delete=models.CASCADE,
                                   related_name='interactions')
    action     = models.CharField(max_length=20, choices=ACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job', 'action')
        indexes = [models.Index(fields=['user', 'action', 'created_at'])]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.action} — {self.job}'

    @classmethod
    def record(cls, user, job, action):
        """Enregistre une interaction (idempotent)."""
        if not user.is_authenticated:
            return
        cls.objects.get_or_create(user=user, job=job, action=action)


class Message(models.Model):
    """Messagerie interne recruteur ↔ candidat."""
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='messages')
    sender      = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='sent_messages')
    content     = models.TextField()
    sent_at     = models.DateTimeField(auto_now_add=True)
    is_read     = models.BooleanField(default=False)

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return 'Message de %s' % self.sender
