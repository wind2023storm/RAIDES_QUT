from django.contrib import admin
from . import models
from django.utils.html import format_html


class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'subject', 'body')
    search_fields = ( 'name', 'email', 'subject', 'body' )


admin.site.register(models.ContactMessage, ContactMessageAdmin)