import json
import math
from http import HTTPStatus

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Count, Case, When, IntegerField, Q, Sum, F
from django.template.loader import get_template

from notification.models import Notification, NotificationStatus
from project.models import Project


class NotificationConsumer(AsyncWebsocketConsumer):
    group_name = None
    user = None
    notifications_per_page = 5

    async def connect(self):
        self.user = self.scope['user']

        # Only let authenticated users connect to this websocket
        if self.user.is_authenticated:
            self.group_name = f"user-notifications-{self.user.id}"

            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, code):
        # Authenticated users should be removed from the group
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # Exit early if they're not authenticated and close their connection
        if not self.user.is_authenticated:
            return

        # Receiving a message from the user
        data = json.loads(text_data)
        message_type = data.get('type', None)

        # Handle the message types, database functions must return an event compatible with
        # one of the send functions, e.g., send_notifications or send_message
        if message_type == 'page':
            page = data.get('page', None)
            event = await self.db_get_paginated_notifications(page)
        elif message_type == 'read':
            note_id = data.get('id', None)
            event = await self.db_mark_as_read(id=note_id)
        elif message_type == 'all_read':
            event = await self.db_mark_as_read()
        elif message_type == 'clear':
            event = await self.db_clear_notifications()
        else:
            return

        # Send the event through the proper function
        await self.channel_layer.group_send(self.group_name, event)

    @database_sync_to_async
    def db_get_paginated_notifications(self, page):
        # Retrieve the notifications from the database or any other data source
        all_notifications = NotificationStatus.objects.filter(user=self.user).select_related('notification')

        # Create a Paginator object
        paginator = Paginator(all_notifications, self.notifications_per_page)

        # Get the specified page
        notifications = paginator.get_page(page)

        return {
            'type': 'send_notifications',
            'notifications': notifications
        }

    @database_sync_to_async
    def db_mark_as_read(self, **query_dict):
        """Marks a queryset of notifications as read."""
        queryset = NotificationStatus.objects.filter(**query_dict, user=self.user).select_related('notification')
        queryset.update(is_read=True)

        for obj in queryset:
            obj.save()

        return {
            'type': 'send_message',
            'message': {**{
                'type': 'read',
                'code': HTTPStatus.OK,
            }, **query_dict}
        }

    @database_sync_to_async
    def db_clear_notifications(self):
        NotificationStatus.objects.filter(user=self.user).delete()

        return {
            'type': 'send_message',
            'message': {
                'type': 'clear',
                'code': HTTPStatus.OK,
                'message': 'success'
            }
        }

    @database_sync_to_async
    def get_notification_counts(self):
        """Returns tuple of all notification counts and read counts"""
        result = NotificationStatus.objects.filter(user=self.user).aggregate(
            count=Count('id'),
            unread_count=Count('id', filter=Q(is_read=False))
        )

        return result['count'], result['unread_count']

    async def send_notifications(self, event):
        # Render the message as html
        notification_template = await sync_to_async(get_template)('notification/notification.html')
        html = await sync_to_async(notification_template.render)(event)

        # Send message to websocket
        total_count, unread_count = await self.get_notification_counts()

        context = {
            'type': 'notification',
            'total_count': total_count,
            'unread_count': unread_count,
            'html': html,
            'code': HTTPStatus.OK
        }

        await self.send(text_data=json.dumps(context))

    async def send_message(self, event):
        """Sends a message as JSON, where the keyword arguments represent the dictionary."""
        message = event['message']

        # Send message to websocket
        total_count, unread_count = await self.get_notification_counts()

        event = {
            **message,
            'total_count': total_count,
            'unread_count': unread_count,
        }

        await self.send(text_data=json.dumps(event))
