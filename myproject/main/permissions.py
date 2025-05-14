from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Custom permission to only allow admins to access certain views.
    """

    def has_permission(self, request, view):
        return request.user and request.user.role == 'admin'


class IsEmployer(permissions.BasePermission):
    """
    Custom permission to only allow employers to access certain views (like job posting).
    """

    def has_permission(self, request, view):
        return request.user and request.user.role == 'employer'


class IsJobSeeker(permissions.BasePermission):
    """
    Custom permission to only allow job seekers to apply for jobs.
    """

    def has_permission(self, request, view):
        return request.user and request.user.role == 'job_seeker'


class IsRecruiterOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow recruiters or admins to review job applications.
    """

    def has_permission(self, request, view):
        return request.user and request.user.role in ['admin', 'recruiter']


class IsAdminUserRole(permissions.BasePermission):
    """
    Custom permission to allow only users with the 'admin' role to access a view.
    """

    def has_permission(self, request, view):
        return request.user and request.user.role == 'admin'
