from django.contrib import admin
from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'training',
        'trainer',
        'issue_date',
        'expiry_date',
        'is_expired',
        'reminder_soon_sent',
        'reminder_expired_sent',
    )
    list_filter = (
        'expiry_date',
        'trainer',
        'reminder_soon_sent',
        'reminder_expired_sent',
    )
    search_fields = (
        'user__username',
        'training__title',
    )
    ordering = ('expiry_date',)
    readonly_fields = ('issue_date',)
    fieldsets = (
        ('Certificate Info', {
            'fields': ('user', 'training', 'trainer')
        }),
        ('Dates', {
            'fields': ('issue_date', 'expiry_date')
        }),
        ('Reminder Status', {
            'fields': ('reminder_soon_sent', 'reminder_expired_sent')
        }),
    )
