from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from main.utils import transaction_atomic
from main.models import Notification
from .models import Institution, InstitutionMember, Job, JobApplication
from .serializers import (
    InstitutionSerializer, InstitutionMemberSerializer,
    JobSerializer, JobApplicationSerializer
)
from .permissions import (
    IsInstitutionAdmin, IsInstitutionCompany,
    IsInstitutionMember, IsJobOwnerOrAdmin,
    IsApplicationOwnerOrJobPoster
)
from main.views import StandardResultsSetPagination

class InstitutionListCreate(generics.ListCreateAPIView):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        institution = serializer.save()
        # Automatically add creator as admin
        InstitutionMember.objects.create(
            user=self.request.user,
            institution=institution,
            role='admin'
        )

class InstitutionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

    def perform_destroy(self, instance):
        Notification.create_admin_notification(
            title="Institution Deleted",
            message=f"Institution '{instance.name}' was deleted by {self.request.user.username}.",
            related_object_id=instance.id,
            related_object_type='institution'
        )
        super().perform_destroy(instance)

class InstitutionMemberListCreate(generics.ListCreateAPIView):
    queryset = InstitutionMember.objects.all()
    serializer_class = InstitutionMemberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        institution_id = self.request.query_params.get('institution_id')
        if institution_id:
            queryset = queryset.filter(institution_id=institution_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save()
        # Notification is handled in the model's save method

class InstitutionMemberDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = InstitutionMember.objects.all()
    serializer_class = InstitutionMemberSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

    def perform_destroy(self, instance):
        Notification.create_notification(
            recipient=instance.user,
            notification_type='institution',
            title="Membership Removed",
            message=f"Your {instance.role} membership at {instance.institution.name} was removed.",
            related_object_id=instance.institution.id,
            related_object_type='institution'
        )
        super().perform_destroy(instance)

class JobListCreate(generics.ListCreateAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated, IsInstitutionCompany]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.query_params.get('search')
        institution_id = self.request.query_params.get('institution_id')
        job_type = self.request.query_params.get('job_type')
        status = self.request.query_params.get('status')

        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        if institution_id:
            queryset = queryset.filter(institution_id=institution_id)
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def perform_create(self, serializer):
        serializer.save(posted_by=self.request.user)

class JobDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated, IsJobOwnerOrAdmin]

    def perform_update(self, serializer):
        old_status = self.get_object().status
        instance = serializer.save()
        if old_status != instance.status:
            Notification.create_admin_notification(
                title="Job Status Updated",
                message=f"Job '{instance.title}' status changed to {instance.status} by {self.request.user.username}.",
                related_object_id=instance.id,
                related_object_type='job'
            )

    def perform_destroy(self, instance):
        Notification.create_admin_notification(
            title="Job Deleted",
            message=f"Job '{instance.title}' was deleted by {self.request.user.username}.",
            related_object_id=instance.id,
            related_object_type='job'
        )
        super().perform_destroy(instance)

class JobApplicationListCreate(generics.ListCreateAPIView):
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        job_id = self.request.query_params.get('job_id')
        user_id = self.request.query_params.get('user_id')
        status = self.request.query_params.get('status')

        if job_id:
            queryset = queryset.filter(job_id=job_id)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class JobApplicationDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated, IsApplicationOwnerOrJobPoster]

    def perform_update(self, serializer):
        instance = serializer.save()
        # Notification for status change is handled in the model's save method

    def perform_destroy(self, instance):
        Notification.create_notification(
            recipient=instance.user,
            notification_type='job_application',
            title="Job Application Removed",
            message=f"Your application for '{instance.job.title}' was removed.",
            related_object_id=instance.id,
            related_object_type='job_application'
        )
        super().perform_destroy(instance)
