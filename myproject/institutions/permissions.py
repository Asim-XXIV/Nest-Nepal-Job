from rest_framework.permissions import BasePermission
from .models import InstitutionMember

class IsInstitutionAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and InstitutionMember.objects.filter(
            user=request.user, role='admin'
        ).exists()

class IsInstitutionCompany(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and InstitutionMember.objects.filter(
            user=request.user, role='company'
        ).exists()

class IsInstitutionMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and InstitutionMember.objects.filter(
            user=request.user, institution=obj.institution
        ).exists()

class IsJobOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (
            obj.posted_by == request.user or
            InstitutionMember.objects.filter(user=request.user, role='admin').exists()
        )

class IsApplicationOwnerOrJobPoster(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (
            obj.user == request.user or
            obj.job.posted_by == request.user or
            InstitutionMember.objects.filter(user=request.user, role='admin').exists()
        )
