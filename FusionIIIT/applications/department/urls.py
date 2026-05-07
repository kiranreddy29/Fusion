from django.conf.urls import url
from django.urls import path, include

from . import views

app_name = 'dep'

urlpatterns = [

    url(r'^$', views.dep_main, name='dep'),
    url(r'^facView/$', views.faculty_view, name='faculty_view'),
    url(r'^staffView/$', views.staff_view, name='staff_view'),
    url(r'^All_Students/(?P<bid>[0-9]+)/$', views.all_students, name='all_students'),
    url(r'^alumni/$', views.alumni, name='alumni'),
    url(r'^approved/$', views.approved, name='approved'),
    url(r'^deny/$', views.deny, name='deny'),

    # Announcements (DEPT-UC-001, 002, 003)
    url(r'^announcements/$', views.announcements_list, name='announcements_list'),
    url(r'^announcements/create/$', views.create_announcement, name='create_announcement'),
    url(r'^announcements/(?P<id>[^/]+)/delete/$', views.delete_announcement, name='delete_announcement'),

    # Stock Management (DEPT-UC-004, 005, 006)
    url(r'^stock/request/$', views.stock_request, name='stock_request'),
    url(r'^stock/(?P<id>\d+)/approve/$', views.stock_approve, name='stock_approve'),
    url(r'^stock/(?P<id>\d+)/issue/$', views.stock_issue, name='stock_issue'),

    # Feedback (DEPT-UC-007, 008)
    path('feedback/submit/', views.submit_feedback, name='submit_feedback'),
    path('feedback/<int:id>/resolve/', views.resolve_feedback, name='resolve_feedback'),
    path('timetable/', views.timetable_list, name='timetable_list'),
    path('timetable', views.timetable_list),
    path('timetable/create/', views.timetable_create, name='timetable_create'),
    path('timetable/create', views.timetable_create),
    path('timetable/upload/', views.timetable_upload, name='timetable_upload'),
    path('timetable/upload', views.timetable_upload),
    path('profile/', views.user_profile, name='user_profile'),
    path('labs/', views.labs_list, name='labs_list'),
    path('facilities/', views.facilities_list, name='facilities_list'),
    path('resources/', views.labs_list, name='resources_list'), # Aligning with UC-011
    path('notifications/', views.announcements_list, name='notifications_list'),
    path('notifications/send/', views.create_announcement, name='notifications_send'), # Aligning with UC-013
    path('changes/<str:id>/approve/', views.stock_approve, name='change_approve'), 
    path('changes/<str:id>/', views.view_change, name='view_change'),
    path('api/', include('applications.department.api.urls')),
    
]