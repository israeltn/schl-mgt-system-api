from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal
from apps.accounts.views import IsSchoolOwnerOrSuperAdmin, IsOfficeAccount, IsStudent
from .models import (
    FeeStructure, FeeRecord, PaymentHistory, Invoice, 
    InvoiceItem, DiscountScheme, StudentDiscount
)
from .serializers import (
    FeeStructureSerializer, FeeRecordSerializer, FeeRecordUpdateSerializer,
    PaymentHistorySerializer, InvoiceSerializer, InvoiceCreateSerializer,
    DiscountSchemeSerializer, StudentDiscountSerializer, BulkPaymentSerializer,
    StudentFeeStatusSerializer, FeeAnalyticsSerializer, PaymentReceiptSerializer
)

class FeeStructureListView(generics.ListCreateAPIView):
    """List and create fee structures"""
    serializer_class = FeeStructureSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        session_id = self.request.query_params.get('session')
        class_id = self.request.query_params.get('class')
        
        if user.is_super_admin:
            queryset = FeeStructure.objects.all()
        elif user.is_school_owner:
            queryset = FeeStructure.objects.filter(school__owner=user)
        elif user.school:
            queryset = FeeStructure.objects.filter(school=user.school)
        else:
            queryset = FeeStructure.objects.none()
        
        if session_id:
            queryset = queryset.filter(academic_session_id=session_id)
        if class_id:
            queryset = queryset.filter(class_level_id=class_id)
        
        return queryset
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.is_school_owner:
            school = user.owned_schools.first()
            serializer.save(school=school)
        elif user.school:
            serializer.save(school=user.school)

class FeeStructureDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete fee structure"""
    serializer_class = FeeStructureSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return FeeStructure.objects.all()
        elif user.is_school_owner:
            return FeeStructure.objects.filter(school__owner=user)
        elif user.school:
            return FeeStructure.objects.filter(school=user.school)
        return FeeStructure.objects.none()

class FeeRecordListView(generics.ListCreateAPIView):
    """List and create fee records"""
    serializer_class = FeeRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        student_id = self.request.query_params.get('student')
        term_id = self.request.query_params.get('term')
        status_filter = self.request.query_params.get('status')
        
        if user.is_super_admin:
            queryset = FeeRecord.objects.all()
        elif user.is_school_owner:
            queryset = FeeRecord.objects.filter(student__user__school__owner=user)
        elif user.is_office_account:
            queryset = FeeRecord.objects.filter(student__user__school=user.school)
        elif user.is_student:
            queryset = FeeRecord.objects.filter(student__user=user)
        elif user.school:
            queryset = FeeRecord.objects.filter(student__user__school=user.school)
        else:
            queryset = FeeRecord.objects.none()
        
        # Apply filters
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if term_id:
            queryset = queryset.filter(term_id=term_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.select_related('student', 'fee_structure', 'term')

class FeeRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete fee record"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return FeeRecordUpdateSerializer
        return FeeRecordSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return FeeRecord.objects.all()
        elif user.is_school_owner:
            return FeeRecord.objects.filter(student__user__school__owner=user)
        elif user.is_office_account:
            return FeeRecord.objects.filter(student__user__school=user.school)
        elif user.is_student:
            return FeeRecord.objects.filter(student__user=user)
        elif user.school:
            return FeeRecord.objects.filter(student__user__school=user.school)
        return FeeRecord.objects.none()
    
    def perform_update(self, serializer):
        # Record payment history when payment is made
        instance = self.get_object()
        old_amount = instance.amount_paid
        new_amount = serializer.validated_data.get('amount_paid', old_amount)
        
        if new_amount > old_amount:
            payment_amount = new_amount - old_amount
            PaymentHistory.objects.create(
                fee_record=instance,
                amount=payment_amount,
                payment_date=serializer.validated_data.get('payment_date', timezone.now().date()),
                payment_method=serializer.validated_data.get('payment_method', 'cash'),
                payment_reference=serializer.validated_data.get('payment_reference', ''),
                remarks=serializer.validated_data.get('remarks', ''),
                recorded_by=self.request.user
            )
        
        serializer.save(recorded_by=self.request.user)

# Payment processing
@api_view(['POST'])
@permission_classes([IsOfficeAccount])
def process_bulk_payment(request):
    """Process bulk payment for multiple fee records"""
    serializer = BulkPaymentSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        user = request.user
        
        payments_processed = []
        total_amount = Decimal('0.00')
        
        with transaction.atomic():
            for record_data in data['fee_records']:
                fee_record = get_object_or_404(
                    FeeRecord,
                    id=record_data['fee_record_id'],
                    student__user__school=user.school
                )
                
                payment_amount = Decimal(str(record_data['amount']))
                new_total_paid = fee_record.amount_paid + payment_amount
                
                # Update fee record
                fee_record.amount_paid = new_total_paid
                fee_record.payment_date = data['payment_date']
                fee_record.payment_method = data['payment_method']
                fee_record.payment_reference = data.get('payment_reference', '')
                fee_record.remarks = data.get('remarks', '')
                fee_record.recorded_by = user
                fee_record.save()
                
                # Create payment history
                PaymentHistory.objects.create(
                    fee_record=fee_record,
                    amount=payment_amount,
                    payment_date=data['payment_date'],
                    payment_method=data['payment_method'],
                    payment_reference=data.get('payment_reference', ''),
                    remarks=data.get('remarks', ''),
                    recorded_by=user
                )
                
                payments_processed.append({
                    'fee_record_id': fee_record.id,
                    'student_name': fee_record.student.user.get_full_name(),
                    'amount_paid': payment_amount,
                    'new_status': fee_record.status
                })
                total_amount += payment_amount
        
        return Response({
            'message': f'Processed {len(payments_processed)} payments',
            'total_amount': total_amount,
            'payments': payments_processed
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsSchoolOwnerOrSuperAdmin])
def generate_fee_records(request):
    """Generate fee records for students based on fee structure"""
    term_id = request.data.get('term_id')
    class_id = request.data.get('class_id')
    fee_structure_ids = request.data.get('fee_structure_ids', [])
    
    if not term_id or not fee_structure_ids:
        return Response({
            'error': 'term_id and fee_structure_ids are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    from apps.academics.models import Term
    from apps.students.models import Student
    
    term = get_object_or_404(Term, id=term_id)
    
    # Get students
    if class_id:
        students = Student.objects.filter(current_class_id=class_id, is_active=True)
    else:
        user = request.user
        if user.is_school_owner:
            students = Student.objects.filter(
                user__school__owner=user,
                is_active=True
            )
        else:
            students = Student.objects.filter(is_active=True)
    
    fee_structures = FeeStructure.objects.filter(id__in=fee_structure_ids)
    
    records_created = []
    with transaction.atomic():
        for student in students:
            for fee_structure in fee_structures:
                # Check if record already exists
                existing_record = FeeRecord.objects.filter(
                    student=student,
                    fee_structure=fee_structure,
                    term=term
                ).first()
                
                if not existing_record:
                    # Calculate due date (default: 30 days from term start)
                    due_date = term.start_date
                    if term.start_date:
                        from datetime import timedelta
                        due_date = term.start_date + timedelta(days=30)
                    
                    fee_record = FeeRecord.objects.create(
                        student=student,
                        fee_structure=fee_structure,
                        term=term,
                        amount_due=fee_structure.amount,
                        due_date=due_date
                    )
                    records_created.append(fee_record)
    
    return Response({
        'message': f'Generated {len(records_created)} fee records',
        'records_count': len(records_created)
    })

# Student fee status and analytics
@api_view(['GET'])
@permission_classes([IsStudent])
def student_fee_status(request):
    """Get fee status for the logged-in student"""
    student = request.user.student_profile
    
    fee_records = student.fee_records.all()
    
    total_due = sum([record.amount_due for record in fee_records])
    total_paid = sum([record.amount_paid for record in fee_records])
    outstanding = total_due - total_paid
    
    # Determine overall status
    if outstanding == 0:
        overall_status = 'cleared'
    elif total_paid > 0:
        overall_status = 'partial'
    else:
        overall_status = 'pending'
    
    # Get last payment date
    last_payment = fee_records.filter(
        amount_paid__gt=0
    ).order_by('-payment_date').first()
    
    status_data = {
        'student_id': student.student_id,
        'student_name': student.user.get_full_name(),
        'total_fees_due': total_due,
        'total_paid': total_paid,
        'outstanding_balance': outstanding,
        'overall_status': overall_status,
        'last_payment_date': last_payment.payment_date if last_payment else None
    }
    
    serializer = StudentFeeStatusSerializer(status_data)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsSchoolOwnerOrSuperAdmin])
def fee_analytics(request):
    """Get fee collection analytics"""
    user = request.user
    term_id = request.query_params.get('term')
    class_id = request.query_params.get('class')
    
    # Build queryset
    if user.is_super_admin:
        queryset = FeeRecord.objects.all()
    elif user.is_school_owner:
        queryset = FeeRecord.objects.filter(student__user__school__owner=user)
    else:
        queryset = FeeRecord.objects.none()
    
    if term_id:
        queryset = queryset.filter(term_id=term_id)
    if class_id:
        queryset = queryset.filter(student__current_class_id=class_id)
    
    # Calculate analytics
    total_due = queryset.aggregate(Sum('amount_due'))['amount_due__sum'] or 0
    total_collected = queryset.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    outstanding = total_due - total_collected
    
    collection_rate = (total_collected / total_due * 100) if total_due > 0 else 0
    
    # Status counts
    total_students = queryset.values('student').distinct().count()
    students_cleared = queryset.filter(status='cleared').values('student').distinct().count()
    students_pending = queryset.filter(status='pending').values('student').distinct().count()
    students_partial = queryset.filter(status='partial').values('student').distinct().count()
    
    analytics_data = {
        'total_students': total_students,
        'total_fees_due': total_due,
        'total_collected': total_collected,
        'outstanding_amount': outstanding,
        'collection_rate': round(collection_rate, 2),
        'students_cleared': students_cleared,
        'students_pending': students_pending,
        'students_partial': students_partial
    }
    
    serializer = FeeAnalyticsSerializer(analytics_data)
    return Response(serializer.data)

# Invoice Views
class InvoiceListView(generics.ListCreateAPIView):
    """List and create invoices"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return InvoiceCreateSerializer
        return InvoiceSerializer
    
    def get_queryset(self):
        user = self.request.user
        student_id = self.request.query_params.get('student')
        status_filter = self.request.query_params.get('status')
        
        if user.is_super_admin:
            queryset = Invoice.objects.all()
        elif user.is_school_owner:
            queryset = Invoice.objects.filter(student__user__school__owner=user)
        elif user.is_office_account:
            queryset = Invoice.objects.filter(student__user__school=user.school)
        elif user.is_student:
            queryset = Invoice.objects.filter(student__user=user)
        elif user.school:
            queryset = Invoice.objects.filter(student__user__school=user.school)
        else:
            queryset = Invoice.objects.none()
        
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.select_related('student', 'academic_session', 'term')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class InvoiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete invoice"""
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Invoice.objects.all()
        elif user.is_school_owner:
            return Invoice.objects.filter(student__user__school__owner=user)
        elif user.is_office_account:
            return Invoice.objects.filter(student__user__school=user.school)
        elif user.is_student:
            return Invoice.objects.filter(student__user=user)
        elif user.school:
            return Invoice.objects.filter(student__user__school=user.school)
        return Invoice.objects.none()

# Discount management
class DiscountSchemeListView(generics.ListCreateAPIView):
    """List and create discount schemes"""
    serializer_class = DiscountSchemeSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return DiscountScheme.objects.all()
        elif user.is_school_owner:
            return DiscountScheme.objects.filter(school__owner=user)
        elif user.school:
            return DiscountScheme.objects.filter(school=user.school)
        return DiscountScheme.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.is_school_owner:
            school = user.owned_schools.first()
            serializer.save(school=school)
        elif user.school:
            serializer.save(school=user.school)

class StudentDiscountListView(generics.ListCreateAPIView):
    """List and create student discounts"""
    serializer_class = StudentDiscountSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        student_id = self.request.query_params.get('student')
        
        if user.is_super_admin:
            queryset = StudentDiscount.objects.all()
        elif user.is_school_owner:
            queryset = StudentDiscount.objects.filter(student__user__school__owner=user)
        elif user.school:
            queryset = StudentDiscount.objects.filter(student__user__school=user.school)
        else:
            queryset = StudentDiscount.objects.none()
        
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        return queryset.select_related('student', 'discount_scheme', 'academic_session')
    
    def perform_create(self, serializer):
        serializer.save(applied_by=self.request.user)