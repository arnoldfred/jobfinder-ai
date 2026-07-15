from django.urls import path
from . import views
app_name = 'applications'
urlpatterns = [
    path('',                           views.history,         name='history'),
    path('apply/<int:pk>/',            views.apply,           name='apply'),
    path('<int:pk>/',                  views.app_detail,      name='detail'),
    path('<int:pk>/withdraw/',         views.withdraw,        name='withdraw'),
    path('<int:pk>/status/',           views.update_status,   name='update_status'),
    path('<int:app_pk>/message/',      views.send_message,    name='send_message'),
    path('job/<int:job_pk>/',          views.job_applications,name='job_apps'),
    path('notifications/',             views.notifications,   name='notifications'),
    path('notifications/read/',        views.mark_read,       name='mark_read'),
    path('notifications/count/',       views.get_badge_counts, name='badge_counts'),
    path('notifications/unread/',      views.unread_count,     name='unread_count'),
    path('notifications/read-type/<str:notif_type>/', views.mark_type_read, name='mark_type_read'),
]
