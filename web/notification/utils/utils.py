from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.urls import reverse

from notification.models import Notification, NotificationStatus


User = get_user_model()


def notify_users(user_from, users_to, summary, target=None, url=None):
    """Creates a notification and sends an instance of it to each user in the supplied queryset.

    Note that the notification is not sent to the actor as they are likely aware of the action they've
    commited.

    Parameters
    ----------
    user_from : User
        The user who instantiated the notification.
    users_to : List[User]
        The users whomst the notification is to be sent
    summary : str
        Notification summary of what event occured
    target : object, optional
        An object related to the notification
    url : str, optional
        The URL in which the user would be redirected to on interaction
    """
    # Create the initial notification
    notification = Notification.objects.create(
        user_from=user_from,
        summary=summary,
        target=target,
        url=url
    )

    # Create a NotificationStatus for each user in the list
    for user in users_to:
        notification.status.create(user=user)


def notify_project_members(project, user_from, summary, target=None, url=None):
    """Same as `notify_users()` except the query for project members is done automatically.
        If target or url are not supplied, they will default to the project/project url."""
    notify_users(
        user_from=user_from,
        users_to=User.objects.filter(memberships__project=project).exclude(id=user_from.id).all(),
        summary=summary,
        target=target if target else project,
        url=url if url else reverse('project:dashboard', kwargs={'slug': project.slug})
    )

