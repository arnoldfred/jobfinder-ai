from django.urls import path
from . import views
app_name = 'accounts'
urlpatterns = [
    path('login/',  views.auth_view, name='auth'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # Expériences
    path('profile/experience/<int:pk>/delete/',  views.delete_experience,  name='delete_experience'),
    path('profile/experience/<int:pk>/update/',  views.update_experience,  name='update_experience'),
    
    # Formations
    path('profile/education/<int:pk>/delete/',   views.delete_education,   name='delete_education'),
    path('profile/education/<int:pk>/update/',   views.update_education,   name='update_education'),
    
    # Compétences
    path('profile/skill/<int:pk>/delete/',       views.delete_skill,       name='delete_skill'),
    
    # CV Import
    path('profile/apply-cv-import/',              views.apply_cv_import,    name='apply_cv_import'),
]
