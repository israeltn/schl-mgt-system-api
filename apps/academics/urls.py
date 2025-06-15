from django.urls import path
from .views import (
    # Academic Sessions
    AcademicSessionListView, AcademicSessionDetailView,
    
    # Terms
    TermListView, TermDetailView,
    
    # Subjects
    SubjectListView, SubjectDetailView,
    
    # Classes
    ClassListView, ClassDetailView,
    
    # Teacher Assignments
    TeacherAssignmentListView, TeacherAssignmentDetailView,
    
    # Teacher-specific views
    get_teacher_assignments, get_teacher_classes,
    
    # Bulk operations
    bulk_create_classes, bulk_create_subjects
)

urlpatterns = [
    # Academic Sessions
    path('sessions/', AcademicSessionListView.as_view(), name='academic_session_list'),
    path('sessions/<int:pk>/', AcademicSessionDetailView.as_view(), name='academic_session_detail'),
    
    # Terms
    path('terms/', TermListView.as_view(), name='term_list'),
    path('terms/<int:pk>/', TermDetailView.as_view(), name='term_detail'),
    
    # Subjects
    path('subjects/', SubjectListView.as_view(), name='subject_list'),
    path('subjects/<int:pk>/', SubjectDetailView.as_view(), name='subject_detail'),
    path('subjects/bulk-create/', bulk_create_subjects, name='bulk_create_subjects'),
    
    # Classes
    path('classes/', ClassListView.as_view(), name='class_list'),
    path('classes/<int:pk>/', ClassDetailView.as_view(), name='class_detail'),
    path('classes/bulk-create/', bulk_create_classes, name='bulk_create_classes'),
    
    # Teacher Assignments
    path('assignments/', TeacherAssignmentListView.as_view(), name='teacher_assignment_list'),
    path('assignments/<int:pk>/', TeacherAssignmentDetailView.as_view(), name='teacher_assignment_detail'),
    
    # Teacher-specific endpoints
    path('teacher/assignments/', get_teacher_assignments, name='teacher_assignments'),
    path('teacher/classes/', get_teacher_classes, name='teacher_classes'),
]