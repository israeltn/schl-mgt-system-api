from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom User model with role-based permissions
    """
    class Role(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'Super Admin'
        SCHOOL_OWNER = 'school_owner', 'School Owner'
        TEACHER = 'teacher', 'Teacher'
        STUDENT = 'student', 'Student'
        PARENT = 'parent', 'Parent'
        OFFICE_ACCOUNT = 'office_account', 'Office Account'
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT
    )
    
    # Additional fields
    phone_number = models.CharField(max_length=15, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    # School relationship (for non-super admin users)
    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"
    
    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN
    
    @property
    def is_school_owner(self):
        return self.role == self.Role.SCHOOL_OWNER
    
    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER
    
    @property
    def is_student(self):
        return self.role == self.Role.STUDENT
    
    @property
    def is_parent(self):
        return self.role == self.Role.PARENT
    
    @property
    def is_office_account(self):
        return self.role == self.Role.OFFICE_ACCOUNT