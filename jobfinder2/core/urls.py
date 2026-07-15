from django.urls import path
from . import views
app_name = 'core'
urlpatterns = [
    path('',                        views.home,                  name='home'),
    path('dashboard/',              views.dashboard,             name='dashboard'),
    path('analytics/',              views.analytics_page,        name='analytics'),

    # ── Espace Admin (préfixe "gestion/" pour éviter le conflit avec /admin/ Django) ──
    path('admin-stats/',                      views.admin_dashboard,    name='admin_dashboard'),
    path('gestion/utilisateurs/',             views.admin_users,        name='admin_users'),
    path('gestion/offres/',                   views.admin_jobs,         name='admin_jobs'),
    path('gestion/candidatures/',             views.admin_applications, name='admin_applications'),
    path('gestion/scraping/',                 views.admin_scraping,     name='admin_scraping'),

    # Actions AJAX admin
    path('gestion/user/<int:pk>/toggle/',     views.admin_toggle_user,  name='admin_toggle_user'),
    path('gestion/user/<int:pk>/promote/',    views.admin_promote_user, name='admin_promote_user'),
    path('gestion/job/<int:pk>/toggle/',      views.admin_toggle_job,   name='admin_toggle_job'),
    path('gestion/job/<int:pk>/feature/',     views.admin_feature_job,  name='admin_feature_job'),
    path('gestion/job/<int:pk>/verify/',      views.admin_verify_job,   name='admin_verify_job'),
    path('gestion/job/<int:pk>/delete/',      views.admin_delete_job,   name='admin_delete_job'),
]
