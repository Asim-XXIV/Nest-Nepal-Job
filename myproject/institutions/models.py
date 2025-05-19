from django.db import models
from django.conf import settings
from main.models import Notification


class Institution(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['name'])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            Notification.create_admin_notification(
                title="New Institution Created",
                message=f"Institution '{self.name}' has been created.",
                related_object_id=self.id,
                related_object_type='institution'
            )


class InstitutionMember(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('company', 'Company'),
        ('job_seeker', 'Job Seeker'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'institution')
        indexes = [models.Index(fields=['user', 'institution'])]

    def __str__(self):
        return f"{self.user.username} - {self.role} at {self.institution.name}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            Notification.create_notification(
                recipient=self.user,
                notification_type='institution',
                title="Institution Membership",
                message=f"You have been added as {self.role} to {self.institution.name}.",
                related_object_id=self.institution.id,
                related_object_type='institution'
            )


class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('internship', 'Internship'),
        ('contract', 'Contract'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    salary_range = models.CharField(max_length=100, blank=True)
    job_type = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs')
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                  related_name='posted_jobs')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['institution']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and self.posted_by:
            Notification.create_notification(
                recipient=self.posted_by,
                notification_type='job',
                title="Job Posted",
                message=f"Your job posting '{self.title}' has been created.",
                related_object_id=self.id,
                related_object_type='job'
            )


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_applications')
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'user')
        indexes = [models.Index(fields=['job', 'status'])]

    def __str__(self):
        return f"{self.user.username} - {self.job.title} ({self.status})"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        old_status = getattr(self, 'status', None) if not is_new else None
        super().save(*args, **kwargs)
        if is_new:
            Notification.create_notification(
                recipient=self.user,
                notification_type='job_application',
                title="Job Application Submitted",
                message=f"Your application for '{self.job.title}' has been submitted.",
                related_object_id=self.id,
                related_object_type='job_application'
            )
            if self.job.posted_by:
                Notification.create_notification(
                    recipient=self.job.posted_by,
                    notification_type='job_application',
                    title="New Job Application",
                    message=f"{self.user.username} applied for your job '{self.job.title}'.",
                    related_object_id=self.id,
                    related_object_type='job_application'
                )
        elif old_status != self.status:
            Notification.create_notification(
                recipient=self.user,
                notification_type='job_application',
                title="Job Application Status Updated",
                message=f"Your application for '{self.job.title}' is now {self.status}.",
                related_object_id=self.id,
                related_object_type='job_application'
            )
