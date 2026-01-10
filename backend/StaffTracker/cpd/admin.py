from django.contrib import admin
from .models import CPDRecord


@admin.register(CPDRecord)
class CPDRecordAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'training',
        'points',
        'earned_date',
    )
    list_filter = (
        'earned_date',
        'training',
    )
    search_fields = (
        'user__username',
        'training__title',
    )
    ordering = ('-earned_date',)
    fieldsets = (
        ('CPD Information', {
            'fields': ('user', 'training', 'points')
        }),
        ('Date', {
            'fields': ('earned_date',)
        }),
    )
