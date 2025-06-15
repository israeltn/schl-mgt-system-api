from django.urls import path
from .views import (
    # Individual Results
    ResultListView, ResultDetailView,
    
    # Term Results
    TermResultListView, TermResultDetailView,
    
    # Student views
    student_results, student_term_result,
    
    # Teacher views
    bulk_result_input,
    
    # Admin operations
    generate_term_results, publish_results,
    
    # Analytics
    class_result_summary, subject_performance,
    
    # Result Template
    ResultTemplateView
)

urlpatterns = [
    # Individual subject results
    path('', ResultListView.as_view(), name='result_list'),
    path('<int:pk>/', ResultDetailView.as_view(), name='result_detail'),
    
    # Term results (aggregated)
    path('term-results/', TermResultListView.as_view(), name='term_result_list'),
    path('term-results/<int:pk>/', TermResultDetailView.as_view(), name='term_result_detail'),
    
    # Student-specific endpoints
    path('student/my-results/', student_results, name='student_results'),
    path('student/term/<int:term_id>/', student_term_result, name='student_term_result'),
    
    # Teacher endpoints
    path('teacher/bulk-input/', bulk_result_input, name='bulk_result_input'),
    
    # Admin operations
    path('generate/', generate_term_results, name='generate_term_results'),
    path('publish/', publish_results, name='publish_results'),
    
    # Analytics and reports
    path('analytics/class-summary/', class_result_summary, name='class_result_summary'),
    path('analytics/subject-performance/', subject_performance, name='subject_performance'),
    
    # Result template
    path('template/', ResultTemplateView.as_view(), name='result_template'),
    path('template/<int:school_id>/', ResultTemplateView.as_view(), name='school_result_template'),
]