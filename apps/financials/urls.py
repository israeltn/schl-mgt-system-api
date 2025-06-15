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

urlpatterns = [
    # Fee Structures
    path('fee-structures/', FeeStructureListView.as_view(), name='fee_structure_list'),
    path('fee-structures/<int:pk>/', FeeStructureDetailView.as_view(), name='fee_structure_detail'),
    
    # Fee Records
    path('fee-records/', FeeRecordListView.as_view(), name='fee_record_list'),
    path('fee-records/<int:pk>/', FeeRecordDetailView.as_view(), name='fee_record_detail'),
    
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