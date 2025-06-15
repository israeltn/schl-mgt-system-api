from django.urls import path
from .views import (
    # Students
    StudentListView, StudentDetailView, StudentProfileView,
    
    # Enrollments
    EnrollmentListView, EnrollmentDetailView,
    
    # Attendance
    AttendanceListView, AttendanceDetailView,
    
    # Custom views
    bulk_attendance, get_class_students, student_dashboard,
    attendance_summary
)

# Import CSV views
from .csv_views import (
    import_students_csv, export_students_csv,
    download_student_csv_template
)

urlpatterns = [
    # Students
    path('', StudentListView.as_view(), name='student_list'),
    path('<int:pk>/', StudentDetailView.as_view(), name='student_detail'),
    path('profile/', StudentProfileView.as_view(), name='student_profile'),
    path('dashboard/', student_dashboard, name='student_dashboard'),
    
    # CSV Import/Export
    path('import/csv/', import_students_csv, name='import_students_csv'),
    path('export/csv/', export_students_csv, name='export_students_csv'),
    path('template/csv/', download_student_csv_template, name='student_csv_template'),
    
    # Enrollments
    path('enrollments/', EnrollmentListView.as_view(), name='enrollment_list'),
    path('enrollments/<int:pk>/', EnrollmentDetailView.as_view(), name='enrollment_detail'),
    
    # Attendance
    path('attendance/', AttendanceListView.as_view(), name='attendance_list'),
    path('attendance/<int:pk>/', AttendanceDetailView.as_view(), name='attendance_detail'),
    path('attendance/bulk/', bulk_attendance, name='bulk_attendance'),
    path('attendance/summary/', attendance_summary, name='attendance_summary'),
    
    # Class-specific views
    path('class/<int:class_id>/', get_class_students, name='class_students'),
]