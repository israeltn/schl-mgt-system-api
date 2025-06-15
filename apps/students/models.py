from django.db import models
from django.conf import settings

class Student(models.Model):
    """
    Student profile extending the User model
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        limit_choices_to={'role': 'student'}
    )
    
    # Student Information
    student_id = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other')
        ]
    )
    address = models.TextField()
    emergency_contact = models.CharField(max_length=15)
    
    # Medical Information
    blood_group = models.CharField(
        max_length=5,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-')
        ],
        blank=True
    )
    medical_conditions = models.TextField(blank=True)
    
    # Parent/Guardian Information
    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='children',
        limit_choices_to={'role': 'parent'},
        null=True,
        blank=True
    )
    guardian_name = models.CharField(max_length=100, blank=True)
    guardian_relationship = models.CharField(max_length=50, blank=True)
    guardian_phone = models.CharField(max_length=15, blank=True)
    guardian_email = models.EmailField(blank=True)
    
    # Academic Information
    admission_date = models.DateField()
    current_class = models.ForeignKey(
        'academics.Class',
        on_delete=models.SET_NULL,
        null=True,
        related_name='students'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id})"
    
    def save(self, *args, **kwargs):
        # Auto-generate student ID if not provided
        if not self.student_id:
            school = self.user.school
            year = self.admission_date.year
            last_student = Student.objects.filter(
                user__school=school,
                student_id__startswith=f"{school.name[:3].upper()}{year}"
            ).order_by('student_id').last()
            
            if last_student:
                last_number = int(last_student.student_id[-4:])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.student_id = f"{school.name[:3].upper()}{year}{new_number:04d}"
        
        super().save(*args, **kwargs)
    
    @property
    def age(self):
        """Calculate student's age"""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def fee_status(self):
        """Get current fee payment status"""
        from apps.financials.models import FeeRecord
        latest_fee = FeeRecord.objects.filter(student=self).order_by('-created_at').first()
        return latest_fee.status if latest_fee else 'pending'

class Enrollment(models.Model):
    """
    Student enrollment in classes for different academic sessions
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    class_enrolled = models.ForeignKey(
        'academics.Class',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    academic_session = models.ForeignKey(
        'academics.AcademicSession',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    
    # Enrollment details
    enrollment_date = models.DateField()
    is_promoted = models.BooleanField(default=False)
    promotion_date = models.DateField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'academic_session']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.class_enrolled.name} ({self.academic_session.name})"

class StudentAttendance(models.Model):
    """
    Daily attendance tracking for students
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=[
            ('present', 'Present'),
            ('absent', 'Absent'),
            ('late', 'Late'),
            ('excused', 'Excused')
        ],
        default='present'
    )
    
    # Additional details
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    
    # Who recorded the attendance
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recorded_attendances'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'date']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.date} - {self.status}"