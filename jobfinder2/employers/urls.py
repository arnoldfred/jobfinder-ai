from django.urls import path
from . import views
app_name = 'employers'
urlpatterns = [
    path('',                          views.employer_dashboard,       name='dashboard'),
    path('suivi/',                    views.job_tracking,             name='tracking'),
    path('setup/',                    views.employer_setup,           name='setup'),
    path('post/',                     views.post_job,                 name='post_job'),
    path('post/<int:pk>/',            views.post_job,                 name='edit_job'),
    path('<int:pk>/toggle/',          views.toggle_job,               name='toggle_job'),
    path('<int:pk>/candidatures/',    views.job_applications,         name='job_apps'),
    path('entreprise/<int:pk>/',      views.public_employer,          name='public'),
    path('candidat/<int:user_pk>/',   views.view_candidate_profile,   name='candidate_profile'),
    # Estimateurs de correspondance
    path('matching/',                 views.candidate_match_overview, name='match_overview'),
    path('matching/<int:job_pk>/<int:candidate_pk>/', views.candidate_match_detail, name='match_detail'),
]
