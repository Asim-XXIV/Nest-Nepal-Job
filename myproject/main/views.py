from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.parsers import MultiPartParser, FormParser
from .models import CustomUser, UserProfile, Notification
from .serializers import (
    RegisterSerializer, LoginSerializer, UserProfileSerializer,
    AdminUserSerializer, PasswordChangeSerializer, NotificationSerializer
)
from .permissions import IsAdminUserRole, IsOwnerOrAdmin
from .utils import transaction_atomic


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class for API views
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class RegisterView(APIView):
    permission_classes = [AllowAny]
    """
    API endpoint for user registration
    """

    @transaction_atomic
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # UserProfile is created via signal
            return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]
    """
    API endpoint for user login
    """

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response = Response({
                "message": "Login successful",
                "role": user.role,
                "user_id": user.id,
                "username": user.username,
            }, status=status.HTTP_200_OK)

            access_expiry = timezone.now() + timedelta(days=1)
            refresh_expiry = timezone.now() + timedelta(days=7)

            response.set_cookie(
                key='access_token',
                value=access_token,
                expires=access_expiry,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite='Lax'
            )
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                expires=refresh_expiry,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite='Lax'
            )

            # Set non-sensitive cookies for frontend use
            response.set_cookie('role', user.role)
            response.set_cookie('user_id', user.id)
            response.set_cookie('username', user.username)

            # Create notification
            Notification.create_notification(
                recipient=user,
                notification_type='account',
                title='Login Successful',
                message=f'Successfully logged in at {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'
            )

            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    API endpoint for user logout
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Create logout notification
            Notification.create_notification(
                recipient=request.user,
                notification_type='account',
                title='Logout Successful',
                message=f'Successfully logged out at {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'
            )

            response = Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)

            # Clear all cookies
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            response.delete_cookie('role')
            response.delete_cookie('user_id')
            response.delete_cookie('username')

            return response
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    API endpoint to change user password
    """
    permission_classes = [IsAuthenticated]

    @transaction_atomic
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"error": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        update_session_auth_hash(request, user)

        # Create notification
        Notification.create_notification(
            recipient=user,
            notification_type='account',
            title='Password Changed',
            message='Your password has been successfully changed.'
        )

        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)


import logging

logger = logging.getLogger(__name__)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        try:
            profile = request.user.userprofile
            serializer = UserProfileSerializer(profile, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

    @transaction_atomic
    def put(self, request):
        try:
            # Log all keys in request.data
            logger.info(f"PUT request data keys: {list(request.data.keys())}")

            # Log if profile_picture is in files or data
            if 'profile_picture' in request.FILES:
                logger.info(
                    f"Received profile_picture file: {request.FILES['profile_picture'].name} size: {request.FILES['profile_picture'].size}")
            else:
                logger.warning("No profile_picture file found in request.FILES")

            profile = request.user.userprofile
            serializer = UserProfileSerializer(
                profile, data=request.data, partial=True, context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                logger.info("Profile updated successfully.")
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                logger.error(f"Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            logger.error("UserProfile does not exist for this user.")
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)


class AdminUserListView(APIView):
    """
    API endpoint for admin to list all users
    """
    permission_classes = [IsAuthenticated, IsAdminUserRole]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        paginator = self.pagination_class()

        # Filter users based on query parameters
        users = CustomUser.objects.all()

        # Search functionality
        search_query = request.query_params.get('search', None)
        if search_query:
            users = users.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query)
            )

        # Role filter
        role = request.query_params.get('role', None)
        if role:
            users = users.filter(role=role)

        # Status filter
        is_active = request.query_params.get('is_active', None)
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            users = users.filter(is_active=is_active)

        # Sort by created_at by default
        users = users.order_by('-created_at')

        # Apply pagination
        paginated_users = paginator.paginate_queryset(users, request)
        serializer = AdminUserSerializer(paginated_users, many=True)

        return paginator.get_paginated_response(serializer.data)


class AdminUserDetailView(APIView):
    """
    API endpoint for admin to manage individual users
    """
    permission_classes = [IsAuthenticated, IsAdminUserRole]

    def get(self, request, user_id):
        user = get_object_or_404(CustomUser, id=user_id)
        profile = getattr(user, 'userprofile', None)

        user_data = AdminUserSerializer(user).data

        if profile:
            profile_data = UserProfileSerializer(profile, context={'request': request}).data
            user_data['profile'] = profile_data
        else:
            user_data['profile'] = None

        return Response(user_data, status=status.HTTP_200_OK)

    @transaction_atomic
    def put(self, request, user_id):
        user = get_object_or_404(CustomUser, id=user_id)
        profile = getattr(user, 'userprofile', None)

        # Update user data
        user_serializer = AdminUserSerializer(user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Update profile data if provided
        if profile and 'profile' in request.data:
            profile_serializer = UserProfileSerializer(
                profile,
                data=request.data.get('profile', {}),
                partial=True,
                context={'request': request}
            )
            if profile_serializer.is_valid():
                profile_serializer.save()
            else:
                return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Create notification for the user
        Notification.create_notification(
            recipient=user,
            notification_type='account',
            title='Account Updated',
            message='Your account has been updated by an administrator.'
        )

        return Response({"message": "User updated successfully"}, status=status.HTTP_200_OK)

    @transaction_atomic
    def delete(self, request, user_id):
        user = get_object_or_404(CustomUser, id=user_id)

        # Prevent self-deletion
        if user == request.user:
            return Response(
                {"error": "You cannot delete your own account"},
                status=status.HTTP_400_BAD_REQUEST
            )

        username = user.username  # Store for notification
        user.delete()

        # Create admin notification
        Notification.create_admin_notification(
            title='User Deleted',
            message=f'User {username} has been deleted by {request.user.username}',
            related_object_type='user'
        )

        return Response({"message": "User deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class RefreshTokenView(APIView):
    """
    API endpoint to refresh access token
    """

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token is None:
            return Response({"error": "Refresh token missing"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            token = RefreshToken(refresh_token)
            access_token = str(token.access_token)

            response = Response({'message': 'Token refreshed successfully'}, status=status.HTTP_200_OK)

            # Set new access token in cookie
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                samesite='Lax',
                secure=False  # Set to True in production with HTTPS
            )

            return response
        except TokenError:
            return Response({"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)


class NotificationListView(APIView):
    """
    API endpoint to list user notifications with pagination
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        paginator = self.pagination_class()
        notifications = Notification.objects.filter(recipient=request.user)

        # Filter by read status if provided
        is_read = request.query_params.get('is_read')
        if is_read is not None:
            is_read_bool = is_read.lower() == 'true'
            notifications = notifications.filter(is_read=is_read_bool)

        # Filter by notification type if provided
        notification_type = request.query_params.get('type')
        if notification_type:
            notifications = notifications.filter(notification_type=notification_type)

        # Apply pagination
        paginated_notifications = paginator.paginate_queryset(notifications, request)
        serializer = NotificationSerializer(paginated_notifications, many=True)

        return paginator.get_paginated_response(serializer.data)


class NotificationDetailView(APIView):
    """
    API endpoint to manage individual notifications
    """
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get(self, request, notification_id):
        notification = get_object_or_404(Notification, id=notification_id)

        # Check permissions
        self.check_object_permissions(request, notification)

        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, notification_id):
        notification = get_object_or_404(Notification, id=notification_id)

        # Check permissions
        self.check_object_permissions(request, notification)

        # Only allow updating the is_read field
        notification.is_read = request.data.get('is_read', notification.is_read)
        notification.save()

        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, notification_id):
        notification = get_object_or_404(Notification, id=notification_id)

        # Check permissions
        self.check_object_permissions(request, notification)

        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationMarkAllReadView(APIView):
    """
    API endpoint to mark all notifications as read
    """
    permission_classes = [IsAuthenticated]

    @transaction_atomic
    def post(self, request):
        count = Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({"message": f"Marked {count} notifications as read"}, status=status.HTTP_200_OK)


class AdminNotificationListView(APIView):
    """
    API endpoint for admin to list all notifications
    """
    permission_classes = [IsAuthenticated, IsAdminUserRole]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        paginator = self.pagination_class()
        notifications = Notification.objects.all()

        # Filter by user if provided
        user_id = request.query_params.get('user_id')
        if user_id:
            notifications = notifications.filter(recipient_id=user_id)

        # Filter by read status if provided
        is_read = request.query_params.get('is_read')
        if is_read is not None:
            is_read_bool = is_read.lower() == 'true'
            notifications = notifications.filter(is_read=is_read_bool)

        # Filter by notification type if provided
        notification_type = request.query_params.get('type')
        if notification_type:
            notifications = notifications.filter(notification_type=notification_type)

        # Apply pagination
        paginated_notifications = paginator.paginate_queryset(notifications, request)
        serializer = NotificationSerializer(paginated_notifications, many=True)

        return paginator.get_paginated_response(serializer.data)


class AdminCreateNotificationView(APIView):
    """
    API endpoint for admin to create notifications for users
    """
    permission_classes = [IsAuthenticated, IsAdminUserRole]

    @transaction_atomic
    def post(self, request):
        recipient_id = request.data.get('recipient_id')
        notification_type = request.data.get('notification_type', 'system')
        title = request.data.get('title')
        message = request.data.get('message')
        related_object_id = request.data.get('related_object_id')
        related_object_type = request.data.get('related_object_type')

        # Validate required fields
        if not title or not message:
            return Response({
                "error": "Title and message are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create notification for specific user or all users
        if recipient_id:
            try:
                recipient = CustomUser.objects.get(id=recipient_id)
                notification = Notification.create_notification(
                    recipient=recipient,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    related_object_id=related_object_id,
                    related_object_type=related_object_type
                )
                serializer = NotificationSerializer(notification)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except CustomUser.DoesNotExist:
                return Response({
                    "error": f"User with ID {recipient_id} does not exist"
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Create notification for all users
            users = CustomUser.objects.filter(is_active=True)
            notifications = []

            for user in users:
                notifications.append(
                    Notification(
                        recipient=user,
                        notification_type=notification_type,
                        title=title,
                        message=message,
                        related_object_id=related_object_id,
                        related_object_type=related_object_type
                    )
                )

            if notifications:
                Notification.objects.bulk_create(notifications)
                return Response({
                    "message": f"Created {len(notifications)} notifications"
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "message": "No active users to notify"
                }, status=status.HTTP_200_OK)


class UserSearchView(APIView):
    """
    API endpoint to search for users
    """
    permission_classes = [IsAuthenticated, IsAdminUserRole]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        paginator = self.pagination_class()
        search_query = request.query_params.get('q', '')

        if not search_query:
            return Response({
                "error": "Search query parameter 'q' is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        users = CustomUser.objects.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(userprofile__full_name__icontains=search_query)
        ).distinct()

        paginated_users = paginator.paginate_queryset(users, request)
        serializer = AdminUserSerializer(paginated_users, many=True)

        return paginator.get_paginated_response(serializer.data)
