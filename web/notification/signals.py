from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from notification.models import NotificationStatus


@receiver(post_save, sender=NotificationStatus)
def send_notification_post_save(sender, instance: NotificationStatus, created, **kwargs):
    """Sends a notification to the user if the model has been created."""
    if created:
        channel_layer = get_channel_layer()
        group_name = f"user-notifications-{instance.user.id}"

        async_to_sync(channel_layer.group_send)(group_name, {
            'type': 'send_notifications',
            'notifications': [instance]
        })


@receiver(post_delete, sender=NotificationStatus)
def delete_notification_if_not_used(sender, instance: NotificationStatus, **kwargs):
    """If a notification no longer has any statuses e.g., all users have marked 'cleared' notifications. Then delete
    the parent notification"""

    # Get the Notification from the status
    notification = instance.notification

    if notification:
        # Count the number of remaining statuses for this notification
        status_count = instance.notification.status.count()

        # If there aren't any left, delete the notification
        if status_count < 1:
            notification.delete()

