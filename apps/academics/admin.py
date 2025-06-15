from django.contrib import admin
from .models import AcademicSession, Term, Subject, Class, TeacherAssignment

@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'school', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active', 'school', 'start_date']
    search_fields = ['name', 'school__name']
    ordering = ['-start_date']

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ['name', 'academic_session', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active', 'academic_session__school', 'start_date']
    search_fields = ['name', 'academic_session__name']
    ordering = ['academic_session', 'start_date']

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'school', 'is_active']
    list_filter = ['is_active', 'school']
    search_fields = ['name', 'code', 'school__name']
    ordering = ['school', 'name']

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'section', 'school', 'academic_session', 'class_teacher', 'current_students_count', 'max_students']
    list_filter = ['is_active', 'school', 'academic_session', 'level']
    search_fields = ['name', 'level', 'school__name']
    ordering = ['school', 'academic_session', 'level', 'section']
    
    def current_students_count(self, obj):
        return obj.current_students_count
    current_students_count.short_description = 'Current Students'

@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'class_assigned', 'subject', 'academic_session', 'is_primary_teacher', 'is_active']
    list_filter = ['is_active', 'is_primary_teacher', 'academic_session', 'class_assigned__school']
    search_fields = ['teacher__first_name', 'teacher__last_name', 'class_assigned__name', 'subject__name']
    ordering = ['academic_session', 'class_assigned', 'subject']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('teacher', 'class_assigned', 'subject', 'academic_session')