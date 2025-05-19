from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    RegisterView, LoginView, LogoutView, ChangePasswordView,
    UserProfileView, AdminUserListView, AdminUserDetailView,
    RefreshTokenView, NotificationListView, NotificationDetailView,
    NotificationMarkAllReadView, AdminNotificationListView,
    AdminCreateNotificationView, UserSearchView
)

urlpatterns = [
                  # Authentication endpoints
                  path('auth/register/', RegisterView.as_view(), name='register'),
                  path('auth/login/', LoginView.as_view(), name='login'),
                  path('auth/logout/', LogoutView.as_view(), name='logout'),
                  path('auth/refresh-token/', RefreshTokenView.as_view(), name='refresh_token'),
                  path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),

                  # User profile endpoints
                  path('users/profile/', UserProfileView.as_view(), name='user_profile'),

                  # Notification endpoints
                  path('notifications/', NotificationListView.as_view(), name='notification_list'),
                  path('notifications/<int:notification_id>/', NotificationDetailView.as_view(),
                       name='notification_detail'),
                  path('notifications/mark-all-read/', NotificationMarkAllReadView.as_view(),
                       name='notification_mark_all_read'),

                  # Admin endpoints
                  path('admin/users/', AdminUserListView.as_view(), name='admin_user_list'),
                  path('admin/users/search/', UserSearchView.as_view(), name='user_search'),
                  path('admin/users/<int:user_id>/', AdminUserDetailView.as_view(), name='admin_user_detail'),
                  path('admin/notifications/', AdminNotificationListView.as_view(), name='admin_notification_list'),
                  path('admin/notifications/create/', AdminCreateNotificationView.as_view(),
                       name='admin_create_notification'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
