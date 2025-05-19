from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Custom permission to only allow admins to access certain views.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')


class IsEmployer(permissions.BasePermission):
    """
    Custom permission to only allow employers to access certain views (like job posting).
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'employer')


class IsJobSeeker(permissions.BasePermission):
    """
    Custom permission to only allow job seekers to apply for jobs.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'job_seeker')


class IsRecruiterOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow recruiters or admins to review job applications.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    request.user.role in ['admin', 'recruiter'])


class IsAdminUserRole(permissions.BasePermission):
    """
    Custom permission to allow only users with the 'admin' role to access a view.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to view/edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Admins can access any object
        if request.user.role == 'admin':
            return True

        # Check if the object has a user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        # For notifications
        elif hasattr(obj, 'recipient'):
            return obj.recipient == request.user
        return False