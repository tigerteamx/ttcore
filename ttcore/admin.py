from django.contrib import admin

from .models import Mail, Event


@admin.register(Mail)
class MailAdmin(admin.ModelAdmin):
    list_display = ['created', 'to_address', 'from_address']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['created', 'user', 'meta']
