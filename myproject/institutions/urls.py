from django.urls import path
from . import views

urlpatterns = [
    path('institutions/', views.InstitutionListCreate.as_view(), name='institution-list-create'),
    path('institution-members/', views.InstitutionMemberListCreate.as_view(), name='institution-member-list-create'),
    path('jobs/', views.JobListCreate.as_view(), name='job-list-create'),
    path('job-applications/', views.JobApplicationListCreate.as_view(), name='job-application-list-create'),
]
