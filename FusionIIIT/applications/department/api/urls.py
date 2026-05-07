from django.conf.urls import url

from . import views
from applications.globals.api.views import profile
urlpatterns = [
    url(r'announcements/$', views.ListCreateAnnouncementView.as_view(),name='announcements'),
    url(r'announcements/delete/$', views.AnnouncementDeleteView.as_view(), name='announcement_delete'),
    url(r'dep-main/$', views.DepMainAPIView.as_view(), name='depmain'),
    url(r'fac-view/$', views.FacAPIView.as_view(), name='facapi'),
    url(r'staff-view/$',views.StaffAPIView.as_view(),name='staffapi'),
    url(r'all-students/(?P<bid>\w+)/$', views.AllStudentsAPIView.as_view(), name='all_students'),
    url(r'student-courses/$', views.StudentCoursesAPIView.as_view(), name='student_courses'),
    url(r'faculty-data/(?P<bid>\w+)/$', views.FacultyDataAPIView.as_view(), name='faculty_data'),
    url(r'ann-data/(?P<bid>\w+)/$', views.AnnouncementsDataAPIView.as_view(), name='ann_data'),
    
    url(r'information/$', views.InformationAPIView.as_view(), name='information'),
    url(r'information/update-create/$', views.InformationUpdateAPIView.as_view(), name='update_create_information'),
    url(r'^labs/$', views.LabListView.as_view(), name='lab-list'),
    url(r'labsadd/$', views.LabAPIView.as_view(), name='add_lab'),
    url(r'labs/delete/$', views.LabDeleteAPIView.as_view(), name='delete_lab'),
    url(r'feedback/create/$', views.FeedbackCreateAPIView.as_view(), name='feedback_create'),
   url(r'feedback/$', views.FeedbackListView.as_view(), name='getfeedback'),
   url(r'feedback/update/(?P<pk>\d+)/$', views.FeedbackUpdateAPIView.as_view(), name='feedback_update'),
   url(r'proposals/create/$', views.DepartmentUpdateProposalCreateView.as_view(), name='dept_proposal_create'),
   url(r'proposals/review/$', views.DepartmentUpdateProposalReviewView.as_view(), name='dept_proposal_review_list'),
   url(r'proposals/review/(?P<pk>\d+)/$', views.DepartmentUpdateProposalReviewView.as_view(), name='dept_proposal_review'),
   url(r'^profile/(?P<username>[\w.@+-]+)/$', profile, name='profile-dynamic'),
    # URL for listing and creating facilities
    url(r'facilities/$', views.FacilityListCreateAPIView.as_view(), name='facility-list-create'),
    
    # URL for retrieving, updating, and deleting a single facility
    url(r'facilities/(?P<pk>\d+)/$', views.FacilityDetailAPIView.as_view(), name='facility-detail'),
    url(r'^facilities/delete/$', views.FacilityBulkDeleteAPIView.as_view(), name='facility-bulk-delete'),

    # Stock management endpoints (T1: DEPT-WF-103)
    url(r'^stock/$', views.StockItemListCreateView.as_view(), name='stock-list-create'),
    url(r'^stock/request/$', views.StockRequestCreateView.as_view(), name='stock-request-create'),
    url(r'^stock/requests/$', views.StockRequestListView.as_view(), name='stock-request-list'),
    url(r'^stock/approve/(?P<pk>\d+)/$', views.StockApprovalView.as_view(), name='stock-approve'),
    url(r'^stock/issue/(?P<pk>\d+)/$', views.StockIssuanceView.as_view(), name='stock-issue'),
    url(r'^stock/logs/$', views.StockLogListView.as_view(), name='stock-logs'),

]
