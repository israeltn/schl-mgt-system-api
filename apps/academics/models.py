from django.db import models
from django.conf import settings

class AcademicSession(models.Model):
    """
    Academic year/session (e.g., 2023/2024)
    """
    name = models.CharField(max_length=50)  # e.g., "2023/2024"
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='academic_sessions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['school', 'name']
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.school.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        if self.is_active:
            # Ensure only one active session per school
            AcademicSession.objects.filter(
                school=self.school, is_active=True
            ).update(is_active=False)
        super().save(*args, **kwargs)

class Term(models.Model):
    """
    Academic terms within a session (e.g., First Term, Second Term)
    """
    name = models.CharField(max_length=50)  # e.g., "First Term"
    academic_session = models.ForeignKey(
        AcademicSession,
        on_delete=models.CASCADE,
        related_name='terms'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['academic_session', 'name']
        ordering = ['start_date']
    
    def __str__(self):
        return f"{self.academic_session.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        if self.is_active:
            # Ensure only one active term per session
            Term.objects.filter(
                academic_session=self.academic_session, is_active=True
            ).update(is_active=False)
        super().save(*args, **kwargs)

class Subject(models.Model):
    """
    Subjects taught in the school
    """
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, blank=True)  # e.g., "MATH", "ENG"
    description = models.TextField(blank=True)
    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='subjects'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['school', 'name']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.school.name})"

class Class(models.Model):
    """
    Classes/Grades in the school (e.g., Grade 5A, JSS 1B)
    """
    name = models.CharField(max_length=50)  # e.g., "Grade 5A"
    level = models.CharField(max_length=20)  # e.g., "Primary 5", "JSS 1"
    section = models.CharField(max_length=10, blank=True)  # e.g., "A", "B"
    
    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='classes'
    )
    academic_session = models.ForeignKey(
        AcademicSession,
        on_delete=models.CASCADE,
        related_name='classes'
    )
    
    # Class details
    max_students = models.IntegerField(default=40)
    class_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_classes',
        limit_choices_to={'role': 'teacher'}
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['school', 'name', 'academic_session']
        ordering = ['level', 'section']
        verbose_name_plural = "Classes"
    
    def __str__(self):
        return f"{self.name} - {self.school.name}"
    
    @property
    def current_students_count(self):
        """Get current number of students in this class"""
        return self.students.filter(is_active=True).count()
    
    @property
    def available_slots(self):
        """Get available student slots"""
        return self.max_students - self.current_students_count

class TeacherAssignment(models.Model):
    """
    Assignment of teachers to classes and subjects
    """
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teaching_assignments',
        limit_choices_to={'role': 'teacher'}
    )
    class_assigned = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='teacher_assignments'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='teacher_assignments'
    )
    academic_session = models.ForeignKey(
        AcademicSession,
        on_delete=models.CASCADE,
        related_name='teacher_assignments'
    )
    
    # Assignment details
    is_primary_teacher = models.BooleanField(
        default=False,
        help_text="Is this the primary teacher for this subject in this class?"
    )
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['teacher', 'class_assigned', 'subject', 'academic_session']
    
    def __str__(self):
        return f"{self.teacher.get_full_name()} - {self.subject.name} - {self.class_assigned.name}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Ensure teacher belongs to the same school
        if self.teacher.school != self.class_assigned.school:
            raise ValidationError("Teacher must belong to the same school as the class.")
        
        # Ensure subject belongs to the same school
        if self.subject.school != self.class_assigned.school:
            raise ValidationError("Subject must belong to the same school as the class.")