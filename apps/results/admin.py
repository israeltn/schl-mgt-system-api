# apps/results/admin.py
from django.contrib import admin
from .models import Result, TermResult, ResultTemplate
# apps/financials/admin.py
from django.contrib import admin
from apps.financials.models import (
    FeeStructure, FeeRecord, PaymentHistory, Invoice, 
    InvoiceItem, DiscountScheme, StudentDiscount
)

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'subject', 'term', 'first_ca', 'second_ca', 
        'exam_marks', 'total_score', 'grade', 'teacher'
    ]
    list_filter = [
        'term', 'subject',  'class_for_term__school',
        'created_at'
    ]
    search_fields = [
        'student__student_id', 'student__user__first_name',
        'student__user__last_name', 'subject__name'
    ]
    ordering = ['-created_at']

@admin.register(TermResult)
class TermResultAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'term', 'class_for_term', 'total_subjects',
        'average_score', 'gpa', 'position', 'is_published'
    ]
    list_filter = [
        'term', 'is_published', 'class_for_term__school',
        'created_at'
    ]
    search_fields = [
        'student__student_id', 'student__user__first_name',
        'student__user__last_name'
    ]
    ordering = ['-created_at']

@admin.register(ResultTemplate)
class ResultTemplateAdmin(admin.ModelAdmin):
    list_display = ['school', 'show_grades', 'show_positions', 'show_gpa']
    list_filter = ['school']



@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'school', 'academic_session', 'class_level',
        'amount', 'payment_frequency', 'is_active'
    ]
    list_filter = [
        'school', 'academic_session', 'payment_frequency', 'is_active'
    ]
    search_fields = ['name', 'school__name']
    ordering = ['school', 'academic_session', 'name']

@admin.register(FeeRecord)
class FeeRecordAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'fee_structure', 'term', 'amount_due',
        'amount_paid', 'balance', 'status', 'due_date'
    ]
    list_filter = [
        'status', 'term', 'fee_structure__school', 'due_date'
    ]
    search_fields = [
        'student__student_id', 'student__user__first_name',
        'student__user__last_name', 'fee_structure__name'
    ]
    ordering = ['-created_at']
    
    def balance(self, obj):
        return obj.balance
    balance.short_description = 'Outstanding Balance'

@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'fee_record', 'amount', 'payment_date', 'payment_method',
        'payment_reference', 'recorded_by'
    ]
    list_filter = [
        'payment_method', 'payment_date', 'recorded_by'
    ]
    search_fields = [
        'fee_record__student__student_id', 'payment_reference'
    ]
    ordering = ['-payment_date']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'student', 'issue_date', 'due_date',
        'total_amount', 'amount_paid', 'status'
    ]
    list_filter = [
        'status', 'issue_date', 'academic_session'
    ]
    search_fields = [
        'invoice_number', 'student__student_id',
        'student__user__first_name', 'student__user__last_name'
    ]
    ordering = ['-issue_date']

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = [
        'invoice', 'description', 'quantity', 'unit_amount', 'total_amount'
    ]
    list_filter = ['invoice__academic_session']

@admin.register(DiscountScheme)
class DiscountSchemeAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'school', 'discount_type', 'discount_value',
        'start_date', 'end_date', 'is_active'
    ]
    list_filter = ['school', 'discount_type', 'is_active']
    search_fields = ['name', 'school__name']

@admin.register(StudentDiscount)
class StudentDiscountAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'discount_scheme', 'academic_session',
        'applied_by', 'is_active'
    ]
    list_filter = [
        'discount_scheme', 'academic_session', 'is_active'
    ]
    search_fields = [
        'student__student_id', 'student__user__first_name',
        'student__user__last_name'
    ]