from django.urls import path
from . import views

urlpatterns = [
    path('institutions/', views.InstitutionListCreate.as_view(), name='institution-list-create'),
    path('institutions/<int:pk>/', views.InstitutionDetail.as_view(), name='institution-detail'),
    path('institution-members/', views.InstitutionMemberListCreate.as_view(), name='institution-member-list-create'),
    path('institution-members/<int:pk>/', views.InstitutionMemberDetail.as_view(), name='institution-member-detail'),
    path('jobs/', views.JobListCreate.as_view(), name='job-list-create'),
    path('jobs/<int:pk>/', views.JobDetail.as_view(), name='job-detail'),
    path('job-applications/', views.JobApplicationListCreate.as_view(), name='job-application-list-create'),
    path('job-applications/<int:pk>/', views.JobApplicationDetail.as_view(), name='job-application-detail'),
]
