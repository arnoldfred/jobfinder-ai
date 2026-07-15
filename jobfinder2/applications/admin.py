from django.contrib import admin
from django.utils.html import format_html
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'job_title', 'status_badge', 'applied_at')
    list_filter = ('status',)
    search_fields = ('user__email', 'job__title', 'job__company')
    readonly_fields = ('applied_at', 'updated_at')
    date_hierarchy = 'applied_at'

    def job_title(self, obj):
        return '%s — %s' % (obj.job.title, obj.job.company) if obj.job else '—'

    def status_badge(self, obj):
        colors = {'sent':'#3b82f6','pending':'#B8960C','interview':'#B8960C','accepted':'#1E7A45','rejected':'#C0392B'}
        c = colors.get(obj.status, '#9ca3af')
        return format_html('<span style="background:{};color:white;padding:2px 9px;border-radius:50px;font-size:11px;font-weight:700">{} {}</span>',
                          c, obj.status_icon, obj.get_status_display())
    status_badge.short_description = 'Statut'
