from django.urls import path
from . import views
app_name = 'jobs'
urlpatterns = [
    path('',                              views.job_list,             name='list'),
    path('saved/',                        views.saved_jobs,           name='saved'),
    path('saved/mark-seen/',             views.mark_saved_seen,      name='mark_saved_seen'),
    path('alertes/',                      views.search_alerts,        name='search_alerts'),
    path('alertes/<int:pk>/delete/',      views.delete_search_alert,  name='delete_alert'),
    path('alertes/<int:pk>/toggle/',      views.toggle_search_alert,  name='toggle_alert'),
    path('<int:pk>/',                     views.job_detail,           name='detail'),
    path('<int:pk>/save/',                views.toggle_save,          name='save'),
    path('<int:pk>/dismiss/',             views.dismiss_job,          name='dismiss'),
    path('<int:pk>/interest/',            views.interest_job,         name='interest'),
    path('<int:pk>/apply/',               views.apply_job,            name='apply'),
]
