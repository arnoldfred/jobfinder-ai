from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "JobFinder AI — Administration"
admin.site.site_title = "JobFinder AI"
admin.site.index_title = "Panneau d'administration"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('auth/', include('accounts.urls')),
    path('jobs/', include('jobs.urls')),
    path('employers/', include('employers.urls')),
    path('applications/', include('applications.urls')),
    path('ai/', include('ai_tools.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'core.views.error_404'
handler500 = 'core.views.error_500'
