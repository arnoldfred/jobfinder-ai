from django.contrib import admin
from django.utils.html import format_html
from .models import EmployerProfile


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'location', 'company_size', 'jobs_count', 'is_verified')
    list_filter = ('is_verified', 'company_size', 'country')
    search_fields = ('company_name', 'user__email', 'industry')
    list_editable = ('is_verified',)

    def jobs_count(self, obj):
        n = obj.jobs_count
        return format_html('<strong style="color:#1E7A45">{}</strong>', n)
    jobs_count.short_description = 'Offres actives'
