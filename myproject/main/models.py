from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, role='job_seeker'):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, role=role)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(username, email, password, role='admin')
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('job_seeker', 'Job Seeker'),
        ('employer', 'Employer'),
        ('admin', 'Admin'),
    )

    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.username} ({self.role})"


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    full_name = models.CharField(max_length=255, blank=True)
    contact_number = models.CharField(max_length=50, blank=True)
    resume_url = models.TextField(blank=True)
    skills = models.JSONField(default=list, blank=True)
    experience = models.TextField(blank=True)
    education = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('account', 'Account'),
        ('profile', 'Profile'),
        ('application', 'Application'),
        ('job', 'Job'),
        ('system', 'System'),
    )

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.notification_type}: {self.title} for {self.recipient.username}"

    @classmethod
    def create_notification(cls, recipient, notification_type, title, message, related_object_id=None,
                            related_object_type=None):
        """
        Utility method to create notifications consistently
        """
        return cls.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            related_object_id=related_object_id,
            related_object_type=related_object_type
        )

    @classmethod
    def create_admin_notification(cls, title, message, related_object_id=None, related_object_type=None):
        """
        Create notification for all admin users
        """
        admin_users = CustomUser.objects.filter(role='admin', is_active=True)
        notifications = []

        for admin in admin_users:
            notifications.append(
                cls(
                    recipient=admin,
                    notification_type='system',
                    title=title,
                    message=message,
                    related_object_id=related_object_id,
                    related_object_type=related_object_type
                )
            )

        if notifications:
            cls.objects.bulk_create(notifications)

        return notifications
