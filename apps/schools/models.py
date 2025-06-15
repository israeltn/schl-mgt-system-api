from django.db import models
from django.conf import settings

class SchoolGroup(models.Model):
    """
    Group of schools under one owner
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='school_groups',
        limit_choices_to={'role': 'school_owner'}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class School(models.Model):
    """
    School model with customization settings
    """
    # Basic Information
    name = models.CharField(max_length=200)
    address = models.TextField()
    contact_email = models.EmailField()
    contact_number = models.CharField(max_length=20)
    website = models.URLField(blank=True)
    
    # Visual Customization
    logo = models.ImageField(upload_to='school_logos/', blank=True, null=True)
    dashboard_primary_color = models.CharField(
        max_length=7, 
        default='#3B82F6',
        help_text='Hex color code for primary theme'
    )
    dashboard_secondary_color = models.CharField(
        max_length=7, 
        default='#1E40AF',
        help_text='Hex color code for secondary theme'
    )
    
    # Relationships
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_schools',
        limit_choices_to={'role': 'school_owner'}
    )
    school_group = models.ForeignKey(
        SchoolGroup,
        on_delete=models.CASCADE,
        related_name='schools',
        null=True,
        blank=True
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def total_students(self):
        """Get total number of students in this school"""
        return self.users.filter(role='student', is_active=True).count()
    
    @property
    def total_teachers(self):
        """Get total number of teachers in this school"""
        return self.users.filter(role='teacher', is_active=True).count()
    
    @property
    def total_classes(self):
        """Get total number of classes in this school"""
        return self.classes.filter(is_active=True).count()

class SMTPSettings(models.Model):
    """
    SMTP configuration for each school
    """
    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
        related_name='smtp_settings'
    )
    
    # SMTP Configuration
    host = models.CharField(max_length=100, default='smtp.gmail.com')
    port = models.IntegerField(default=587)
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)
    
    # Authentication
    username = models.EmailField()
    password = models.CharField(max_length=200)  # Should be encrypted in production
    
    # Email Settings
    from_email = models.EmailField()
    from_name = models.CharField(max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"SMTP Settings for {self.school.name}"