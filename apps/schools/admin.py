from django.contrib import admin
from .models import School, SchoolGroup, SMTPSettings

@admin.register(SchoolGroup)
class SchoolGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'created_at']
    list_filter = ['created_at', 'owner']
    search_fields = ['name', 'owner__username']
    ordering = ['-created_at']

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'contact_email', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'owner']
    search_fields = ['name', 'contact_email', 'owner__username']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'address', 'contact_email', 'contact_number', 'website')
        }),
        ('Customization', {
            'fields': ('logo', 'dashboard_primary_color', 'dashboard_secondary_color')
        }),
        ('Relationships', {
            'fields': ('owner', 'school_group')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

@admin.register(SMTPSettings)
class SMTPSettingsAdmin(admin.ModelAdmin):
    list_display = ['school', 'host', 'port', 'username', 'is_active']
    list_filter = ['is_active', 'host', 'port']
    search_fields = ['school__name', 'username']
    
    fieldsets = (
        ('School', {
            'fields': ('school',)
        }),
        ('SMTP Configuration', {
            'fields': ('host', 'port', 'use_tls', 'use_ssl')
        }),
        ('Authentication', {
            'fields': ('username', 'password')
        }),
        ('Email Settings', {
            'fields': ('from_email', 'from_name')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )