from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import InstitutionMember
from main.models import Notification

@receiver(post_save, sender=InstitutionMember)
def notify_institution_member_update(sender, instance, created, **kwargs):
    if not created and instance.role != instance._original_role:
        Notification.create_notification(
            recipient=instance.user,
            notification_type='institution',
            title="Membership Role Updated",
            message=f"Your role at {instance.institution.name} has been updated to {instance.role}.",
            related_object_id=instance.institution.id,
            related_object_type='institution'
        )

    # Store original role for comparison on next save
    instance._original_role = instance.role
