from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from .models import UserProfile, CustomUser, Notification


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Create or update user profile when user is created or updated
    """
    if created:
        UserProfile.objects.create(user=instance)

        # Create notification for the user
        Notification.create_notification(
            recipient=instance,
            notification_type='account',
            title='Welcome to Job Portal',
            message=f'Welcome to the Job Portal, {instance.username}! Complete your profile to get started.'
        )

        # Create notification for admins
        Notification.create_admin_notification(
            title='New User Registration',
            message=f'New user {instance.username} registered as {instance.role}',
            related_object_id=instance.id,
            related_object_type='user'
        )
    else:
        # Ensure the profile exists
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=UserProfile)
def notify_profile_update(sender, instance, created, **kwargs):
    """
    Create notification when user profile is updated
    """
    if not created:
        Notification.create_notification(
            recipient=instance.user,
            notification_type='profile',
            title='Profile Updated',
            message='Your profile has been successfully updated.'
        )
