from django.contrib import admin
from django.utils.html import format_html
from .models import Job, JobSource, JobMatch, SavedJob


@admin.register(JobSource)
class JobSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'jobs_scraped', 'last_sync', 'is_active')
    list_editable = ('is_active',)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'country', 'domain', 'job_type', 'source_type',
                    'is_active', 'is_featured', 'view_count', 'posted_at')
    list_filter = ('country', 'domain', 'job_type', 'source_type', 'is_active', 'is_featured', 'is_remote')
    search_fields = ('title', 'company', 'location', 'description')
    list_editable = ('is_active', 'is_featured')
    readonly_fields = ('view_count', 'posted_at', 'updated_at')
    date_hierarchy = 'posted_at'
    fieldsets = (
        ('Essentiel', {'fields': ('title', 'company', 'company_logo', 'location', 'country', 'is_remote', 'job_type', 'domain')}),
        ('Contenu', {'fields': ('description', 'missions', 'requirements', 'required_skills', 'nice_to_have', 'company_about')}),
        ('Salaire', {'fields': ('salary_min', 'salary_max', 'salary_currency', 'salary_display_text')}),
        ('Source', {'fields': ('source_type', 'scraping_source', 'employer', 'external_url', 'external_id')}),
        ('Statut', {'fields': ('is_active', 'is_verified', 'is_featured', 'deadline', 'view_count', 'posted_at', 'updated_at')}),
    )


@admin.register(JobMatch)
class JobMatchAdmin(admin.ModelAdmin):
    list_display = ('user', 'job_title', 'score_display', 'computed_at')
    list_filter = ('score',)
    ordering = ('-score',)

    def job_title(self, obj):
        return '%s — %s' % (obj.job.title, obj.job.company)

    def score_display(self, obj):
        color = '#1E7A45' if obj.score >= 90 else '#B8960C' if obj.score >= 70 else '#C0392B'
        return format_html('<strong style="color:{}">{} %</strong>', color, obj.score)
    score_display.short_description = 'Score'
