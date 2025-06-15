from rest_framework import serializers
from .models import (
    FeeStructure, FeeRecord, PaymentHistory, Invoice, 
    InvoiceItem, DiscountScheme, StudentDiscount
)

class FeeStructureSerializer(serializers.ModelSerializer):
    """Serializer for FeeStructure model"""
    school_name = serializers.CharField(source='school.name', read_only=True)
    session_name = serializers.CharField(source='academic_session.name', read_only=True)
    class_name = serializers.CharField(source='class_level.name', read_only=True)
    
    class Meta:
        model = FeeStructure
        fields = [
            'id', 'school', 'school_name', 'academic_session', 'session_name',
            'class_level', 'class_name', 'name', 'amount', 'payment_frequency',
            'is_mandatory', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class PaymentHistorySerializer(serializers.ModelSerializer):
    """Serializer for PaymentHistory model"""
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)
    
    class Meta:
        model = PaymentHistory
        fields = [
            'id', 'amount', 'payment_date', 'payment_method',
            'payment_reference', 'remarks', 'recorded_by',
            'recorded_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class FeeRecordSerializer(serializers.ModelSerializer):
    """Serializer for FeeRecord model"""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    fee_name = serializers.CharField(source='fee_structure.name', read_only=True)
    term_name = serializers.CharField(source='term.name', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)
    balance = serializers.ReadOnlyField()
    is_fully_paid = serializers.ReadOnlyField()
    payment_history = PaymentHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = FeeRecord
        fields = [
            'id', 'student', 'student_name', 'student_id', 'fee_structure',
            'fee_name', 'term', 'term_name', 'amount_due', 'amount_paid',
            'status', 'due_date', 'payment_date', 'payment_method',
            'payment_reference', 'remarks', 'recorded_by', 'recorded_by_name',
            'balance', 'is_fully_paid', 'payment_history', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'balance', 'is_fully_paid', 'created_at', 'updated_at']

class FeeRecordUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating fee records (payment processing)"""
    
    class Meta:
        model = FeeRecord
        fields = [
            'amount_paid', 'payment_date', 'payment_method',
            'payment_reference', 'remarks'
        ]

class BulkPaymentSerializer(serializers.Serializer):
    """Serializer for processing bulk payments"""
    fee_records = serializers.ListField(
        child=serializers.DictField()
    )
    payment_date = serializers.DateField()
    payment_method = serializers.CharField(max_length=20)
    payment_reference = serializers.CharField(max_length=100, required=False)
    remarks = serializers.CharField(required=False)
    
    def validate_fee_records(self, value):
        """Validate fee records structure"""
        for record in value:
            if 'fee_record_id' not in record or 'amount' not in record:
                raise serializers.ValidationError(
                    "Each fee record must have 'fee_record_id' and 'amount'"
                )
        return value

class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for InvoiceItem model"""
    fee_name = serializers.CharField(source='fee_structure.name', read_only=True)
    
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'fee_structure', 'fee_name', 'description',
            'quantity', 'unit_amount', 'total_amount'
        ]
        read_only_fields = ['id', 'total_amount']

class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice model"""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    session_name = serializers.CharField(source='academic_session.name', read_only=True)
    term_name = serializers.CharField(source='term.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    balance = serializers.ReadOnlyField()
    items = InvoiceItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'student', 'student_name', 'student_id', 'academic_session',
            'session_name', 'term', 'term_name', 'invoice_number',
            'issue_date', 'due_date', 'total_amount', 'amount_paid',
            'status', 'notes', 'created_by', 'created_by_name',
            'balance', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'invoice_number', 'balance', 'created_at', 'updated_at']

class InvoiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating invoices"""
    items = InvoiceItemSerializer(many=True)
    
    class Meta:
        model = Invoice
        fields = [
            'student', 'academic_session', 'term', 'due_date',
            'notes', 'items'
        ]
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        invoice = Invoice.objects.create(**validated_data)
        
        total_amount = 0
        for item_data in items_data:
            item = InvoiceItem.objects.create(invoice=invoice, **item_data)
            total_amount += item.total_amount
        
        invoice.total_amount = total_amount
        invoice.save()
        return invoice

class DiscountSchemeSerializer(serializers.ModelSerializer):
    """Serializer for DiscountScheme model"""
    school_name = serializers.CharField(source='school.name', read_only=True)
    
    class Meta:
        model = DiscountScheme
        fields = [
            'id', 'school', 'school_name', 'name', 'description',
            'discount_type', 'discount_value', 'applies_to',
            'start_date', 'end_date', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class StudentDiscountSerializer(serializers.ModelSerializer):
    """Serializer for StudentDiscount model"""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    discount_name = serializers.CharField(source='discount_scheme.name', read_only=True)
    session_name = serializers.CharField(source='academic_session.name', read_only=True)
    applied_by_name = serializers.CharField(source='applied_by.get_full_name', read_only=True)
    
    class Meta:
        model = StudentDiscount
        fields = [
            'id', 'student', 'student_name', 'student_id', 'discount_scheme',
            'discount_name', 'academic_session', 'session_name', 'applied_by',
            'applied_by_name', 'reason', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class StudentFeeStatusSerializer(serializers.Serializer):
    """Serializer for student fee status overview"""
    student_id = serializers.CharField()
    student_name = serializers.CharField()
    total_fees_due = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    outstanding_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    overall_status = serializers.CharField()
    last_payment_date = serializers.DateField()

class FeeAnalyticsSerializer(serializers.Serializer):
    """Serializer for fee analytics data"""
    total_students = serializers.IntegerField()
    total_fees_due = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_collected = serializers.DecimalField(max_digits=15, decimal_places=2)
    outstanding_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    collection_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    students_cleared = serializers.IntegerField()
    students_pending = serializers.IntegerField()
    students_partial = serializers.IntegerField()

class PaymentReceiptSerializer(serializers.Serializer):
    """Serializer for payment receipt data"""
    receipt_number = serializers.CharField()
    student_name = serializers.CharField()
    student_id = serializers.CharField()
    payment_date = serializers.DateField()
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.CharField()
    payment_reference = serializers.CharField()
    fee_details = serializers.ListField(
        child=serializers.DictField()
    )
    school_info = serializers.DictField()
    processed_by = serializers.CharField()