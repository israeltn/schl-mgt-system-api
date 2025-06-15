from django.urls import path
from .views import (
    # Fee Structures
    FeeStructureListView, FeeStructureDetailView,
    
    # Fee Records
    FeeRecordListView, FeeRecordDetailView,
    
    # Payment Processing
    process_bulk_payment, generate_fee_records,
    
    # Student Views
    student_fee_status,
    
    # Analytics
    fee_analytics,
    
    # Invoices
    InvoiceListView, InvoiceDetailView,
    
    # Discounts
    DiscountSchemeListView, StudentDiscountListView
)

# Import CSV views for fees
from apps.students.csv_views import (
    import_fees_csv, export_fees_csv,

    download_fee_csv_template, check_import_status

)

urlpatterns = [
    # Fee Structures
    path('fee-structures/', FeeStructureListView.as_view(), name='fee_structure_list'),
    path('fee-structures/<int:pk>/', FeeStructureDetailView.as_view(), name='fee_structure_detail'),
    
    # Fee Records
    path('fee-records/', FeeRecordListView.as_view(), name='fee_record_list'),
    path('fee-records/<int:pk>/', FeeRecordDetailView.as_view(), name='fee_record_detail'),
    
    # Fee CSV Import/Export
    path('fees/import/csv/', import_fees_csv, name='import_fees_csv'),
    path('fees/export/csv/', export_fees_csv, name='export_fees_csv'),
    path('fees/template/csv/', download_fee_csv_template, name='fee_csv_template'),

    path('fees/import/status/<str:task_id>/', check_import_status, name='fee_import_status'),

    
    # Payment Processing
    path('payments/bulk/', process_bulk_payment, name='bulk_payment'),
    path('fee-records/generate/', generate_fee_records, name='generate_fee_records'),
    
    # Student Endpoints
    path('student/fee-status/', student_fee_status, name='student_fee_status'),
    
    # Analytics
    path('analytics/', fee_analytics, name='fee_analytics'),
    
    # Invoices
    path('invoices/', InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/<int:pk>/', InvoiceDetailView.as_view(), name='invoice_detail'),
    
    # Discounts
    path('discount-schemes/', DiscountSchemeListView.as_view(), name='discount_scheme_list'),
    path('student-discounts/', StudentDiscountListView.as_view(), name='student_discount_list'),
]