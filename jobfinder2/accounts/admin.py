from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseAdmin
from django.utils.html import format_html
from .models import User, UserProfile, Skill, Experience, Education


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 0
    fields = ('name', 'category')


class ExpInline(admin.TabularInline):
    model = Experience
    extra = 0
    fields = ('title', 'company', 'start_date', 'is_current')


@admin.register(UserProfile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'desired_title', 'location', 'completion_bar', 'updated_at')
    search_fields = ('user__email', 'user__first_name', 'desired_title', 'location')
    readonly_fields = ('completion_score', 'updated_at')
    inlines = [SkillInline, ExpInline]

    def completion_bar(self, obj):
        p = obj.completion_score
        c = '#1E7A45' if p >= 80 else '#B8960C' if p >= 50 else '#C0392B'
        return format_html(
            '<div style="width:100px;background:#eee;border-radius:4px;overflow:hidden">'
            '<div style="width:{}%;height:10px;background:{}"></div></div> {}%', p, c, p)
    completion_bar.short_description = 'Complétion'


@admin.register(User)
class UserAdmin(BaseAdmin):
    list_display = ('email', 'full_name', 'role', 'plan', 'country', 'is_verified', 'date_joined')
    list_filter = ('role', 'plan', 'is_verified', 'is_active', 'country')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    fieldsets = BaseAdmin.fieldsets + (
        ('JobFinder AI', {'fields': ('role', 'plan', 'country', 'phone', 'is_verified')}),
    )
    add_fieldsets = ((None, {'classes': ('wide',), 'fields': ('email', 'username', 'first_name', 'last_name', 'role', 'country', 'password1', 'password2')}),)

    def full_name(self, obj):
        return obj.get_full_name() or '—'
    full_name.short_description = 'Nom'
