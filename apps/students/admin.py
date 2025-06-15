from django.contrib import admin
from .models import Student, Enrollment, StudentAttendance

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = [
        'student_id', 'get_full_name', 'current_class', 'gender', 
        'admission_date', 'fee_status', 'is_active'
    ]
    list_filter = [
        'is_active', 'gender', 'current_class__school', 'current_class',
        'admission_date'
    ]
    search_fields = [
        'student_id', 'user__first_name', 'user__last_name', 
        'user__email', 'guardian_name'
    ]
    ordering = ['-admission_date']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Student Details', {
            'fields': ('student_id', 'date_of_birth', 'gender', 'address', 
                      'emergency_contact', 'admission_date', 'current_class')
        }),
        ('Medical Information', {
            'fields': ('blood_group', 'medical_conditions')
        }),
        ('Guardian Information', {
            'fields': ('parent', 'guardian_name', 'guardian_relationship',
                      'guardian_phone', 'guardian_email')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'user__first_name'

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'class_enrolled', 'academic_session', 
        'enrollment_date', 'is_promoted', 'is_active'
    ]
    list_filter = [
        'is_active', 'is_promoted', 'academic_session', 
        'class_enrolled__school', 'enrollment_date'
    ]
    search_fields = [
        'student__student_id', 'student__user__first_name',
        'student__user__last_name', 'class_enrolled__name'
    ]
    ordering = ['-enrollment_date']

@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'date', 'status', 'time_in', 'time_out', 'recorded_by'
    ]
    list_filter = [
        'status', 'date', 'student__current_class__school', 
        'student__current_class'
    ]
    search_fields = [
        'student__student_id', 'student__user__first_name',
        'student__user__last_name'
    ]
    ordering = ['-date', 'student']
    date_hierarchy = 'date'