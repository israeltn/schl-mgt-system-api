import csv
import io
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.http import HttpResponse
from django.db import transaction
from django.shortcuts import get_object_or_404
from apps.accounts.views import IsSchoolOwnerOrSuperAdmin
from apps.accounts.models import User
from apps.students.models import Student
from apps.students.serializers import StudentCSVImportSerializer, StudentCSVExportSerializer
from apps.academics.models import Class
from apps.financials.models import FeeRecord, FeeStructure


# Teacher CSV Import/Export Serializers
from rest_framework import serializers

class TeacherCSVImportSerializer(serializers.Serializer):
    """Serializer for CSV import of teachers"""
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, default='defaultpass123')
    phone_number = serializers.CharField(max_length=15, required=False, allow_blank=True)

class TeacherCSVExportSerializer(serializers.ModelSerializer):
    """Serializer for CSV export of teachers"""
    school_name = serializers.CharField(source='school.name')
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'phone_number', 'school_name', 'is_active', 'created_at'
        ]

class FeeCSVImportSerializer(serializers.Serializer):
    """Serializer for CSV import of fees"""
    student_id = serializers.CharField(max_length=20)
    fee_structure_name = serializers.CharField(max_length=100)
    term_name = serializers.CharField(max_length=50)
    amount_due = serializers.DecimalField(max_digits=10, decimal_places=2)
    due_date = serializers.DateField()

class FeeCSVExportSerializer(serializers.Serializer):
    """Serializer for CSV export of fees"""
    student_id = serializers.CharField()
    student_name = serializers.CharField()
    fee_structure_name = serializers.CharField()
    term_name = serializers.CharField()
    amount_due = serializers.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField()
    due_date = serializers.DateField()


# Student CSV Import/Export Views
@api_view(['POST'])
@permission_classes([IsSchoolOwnerOrSuperAdmin])
def import_students_csv(request):
    """Import students from CSV file"""
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    csv_file = request.FILES['file']
    
    if not csv_file.name.endswith('.csv'):
        return Response({'error': 'File must be a CSV'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    school = user.owned_schools.first() if user.is_school_owner else None
    
    if not school and not user.is_super_admin:
        return Response({'error': 'School not found'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Read CSV file
        data_set = csv_file.read().decode('UTF-8')
        io_string = io.StringIO(data_set)
        reader = csv.DictReader(io_string)
        
        created_students = []
        errors = []
        
        with transaction.atomic():
            for row_num, row in enumerate(reader, 1):
                try:
                    # Clean row data
                    cleaned_row = {k: v.strip() if v else '' for k, v in row.items()}
                    
                    # Validate data
                    serializer = StudentCSVImportSerializer(data=cleaned_row)
                    if serializer.is_valid():
                        data = serializer.validated_data
                        
                        # Create user
                        user_data = {
                            'username': data['username'],
                            'email': data['email'],
                            'first_name': data['first_name'],
                            'last_name': data['last_name'],
                            'role': 'student',
                            'school': school
                        }
                        
                        # Check if user already exists
                        if User.objects.filter(username=data['username']).exists():
                            errors.append(f"Row {row_num}: Username '{data['username']}' already exists")
                            continue
                        
                        if User.objects.filter(email=data['email']).exists():
                            errors.append(f"Row {row_num}: Email '{data['email']}' already exists")
                            continue
                        
                        user = User.objects.create_user(**user_data)
                        user.set_password(data['password'])
                        user.save()
                        
                        # Find class if specified
                        current_class = None
                        if data.get('current_class'):
                            current_class = Class.objects.filter(
                                name=data['current_class'],
                                school=school
                            ).first()
                        
                        # Create student
                        student_data = {
                            'user': user,
                            'date_of_birth': data['date_of_birth'],
                            'gender': data['gender'],
                            'address': data['address'],
                            'emergency_contact': data['emergency_contact'],
                            'blood_group': data.get('blood_group', ''),
                            'medical_conditions': data.get('medical_conditions', ''),
                            'guardian_name': data.get('guardian_name', ''),
                            'guardian_relationship': data.get('guardian_relationship', ''),
                            'guardian_phone': data.get('guardian_phone', ''),
                            'guardian_email': data.get('guardian_email', ''),
                            'admission_date': data['admission_date'],
                            'current_class': current_class
                        }
                        
                        student = Student.objects.create(**student_data)
                        created_students.append(student)
                        
                    else:
                        errors.append(f"Row {row_num}: {serializer.errors}")
                        
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
        
        return Response({
            'message': f'Successfully imported {len(created_students)} students',
            'created_count': len(created_students),
            'errors': errors
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsSchoolOwnerOrSuperAdmin])
def export_students_csv(request):
    """Export students to CSV file"""
    user = request.user
    
    if user.is_super_admin:
        students = Student.objects.all()
    elif user.is_school_owner:
        students = Student.objects.filter(user__school__owner=user)
    else:
        students = Student.objects.none()
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students_export.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Student ID', 'First Name', 'Last Name', 'Email', 'Username',
        'Date of Birth', 'Gender', 'Address', 'Emergency Contact',
        'Blood Group', 'Medical Conditions', 'Guardian Name',
        'Guardian Relationship', 'Guardian Phone', 'Guardian Email',
        'Admission Date', 'Current Class', 'School Name', 'Active'
    ])
    
    # Write data
    for student in students:
        serializer = StudentCSVExportSerializer(student)
        data = serializer.data
        writer.writerow([
            data['student_id'], data['first_name'], data['last_name'],
            data['email'], data['username'], data['date_of_birth'],
            data['gender'], data['address'], data['emergency_contact'],
            data['blood_group'], data['medical_conditions'], data['guardian_name'],
            data['guardian_relationship'], data['guardian_phone'], data['guardian_email'],
            data['admission_date'], data['current_class_name'], data['school_name'],
            data['is_active']
        ])
    
    return response


# Teacher CSV Import/Export Views
@api_view(['POST'])
@permission_classes([IsSchoolOwnerOrSuperAdmin])
def import_teachers_csv(request):
    """Import teachers from CSV file"""
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    csv_file = request.FILES['file']
    
    if not csv_file.name.endswith('.csv'):
        return Response({'error': 'File must be a CSV'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    school = user.owned_schools.first() if user.is_school_owner else None
    
    if not school and not user.is_super_admin:
        return Response({'error': 'School not found'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Read CSV file
        data_set = csv_file.read().decode('UTF-8')
        io_string = io.StringIO(data_set)
        reader = csv.DictReader(io_string)
        
        created_teachers = []
        errors = []
        
        with transaction.atomic():
            for row_num, row in enumerate(reader, 1):
                try:
                    # Clean row data
                    cleaned_row = {k: v.strip() if v else '' for k, v in row.items()}
                    
                    # Validate data
                    serializer = TeacherCSVImportSerializer(data=cleaned_row)
                    if serializer.is_valid():
                        data = serializer.validated_data
                        
                        # Check if user already exists
                        if User.objects.filter(username=data['username']).exists():
                            errors.append(f"Row {row_num}: Username '{data['username']}' already exists")
                            continue
                        
                        if User.objects.filter(email=data['email']).exists():
                            errors.append(f"Row {row_num}: Email '{data['email']}' already exists")
                            continue
                        
                        # Create teacher user
                        user_data = {
                            'username': data['username'],
                            'email': data['email'],
                            'first_name': data['first_name'],
                            'last_name': data['last_name'],
                            'phone_number': data.get('phone_number', ''),
                            'role': 'teacher',
                            'school': school
                        }
                        
                        teacher = User.objects.create_user(**user_data)
                        teacher.set_password(data['password'])
                        teacher.save()
                        created_teachers.append(teacher)
                        
                    else:
                        errors.append(f"Row {row_num}: {serializer.errors}")
                        
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
        
        return Response({
            'message': f'Successfully imported {len(created_teachers)} teachers',
            'created_count': len(created_teachers),
            'errors': errors
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsSchoolOwnerOrSuperAdmin])
def export_teachers_csv(request):
    """Export teachers to CSV file"""
    user = request.user
    
    if user.is_super_admin:
        teachers = User.objects.filter(role='teacher')
    elif user.is_school_owner:
        teachers = User.objects.filter(role='teacher', school__owner=user)
    else:
        teachers = User.objects.none()
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="teachers_export.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'ID', 'Username', 'First Name', 'Last Name', 'Email',
        'Phone Number', 'School Name', 'Active', 'Created At'
    ])
    
    # Write data
    for teacher in teachers:
        serializer = TeacherCSVExportSerializer(teacher)
        data = serializer.data
        writer.writerow([
            data['id'], data['username'], data['first_name'],
            data['last_name'], data['email'], data['phone_number'],
            data['school_name'], data['is_active'], data['created_at']
        ])
    
    return response


# Fee CSV Import/Export Views
@api_view(['POST'])
@permission_classes([IsSchoolOwnerOrSuperAdmin])
def import_fees_csv(request):
    """Import fee records from CSV file"""
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    csv_file = request.FILES['file']
    
    if not csv_file.name.endswith('.csv'):
        return Response({'error': 'File must be a CSV'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    school = user.owned_schools.first() if user.is_school_owner else None
    
    if not school and not user.is_super_admin:
        return Response({'error': 'School not found'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Read CSV file
        data_set = csv_file.read().decode('UTF-8')
        io_string = io.StringIO(data_set)
        reader = csv.DictReader(io_string)
        
        created_fees = []
        errors = []
        
        with transaction.atomic():
            for row_num, row in enumerate(reader, 1):
                try:
                    # Clean row data
                    cleaned_row = {k: v.strip() if v else '' for k, v in row.items()}
                    
                    # Validate data
                    serializer = FeeCSVImportSerializer(data=cleaned_row)
                    if serializer.is_valid():
                        data = serializer.validated_data
                        
                        # Find student
                        try:
                            student = Student.objects.get(
                                student_id=data['student_id'],
                                user__school=school
                            )
                        except Student.DoesNotExist:
                            errors.append(f"Row {row_num}: Student with ID '{data['student_id']}' not found")
                            continue
                        
                        # Find fee structure
                        try:
                            fee_structure = FeeStructure.objects.get(
                                name=data['fee_structure_name'],
                                school=school
                            )
                        except FeeStructure.DoesNotExist:
                            errors.append(f"Row {row_num}: Fee structure '{data['fee_structure_name']}' not found")
                            continue
                        
                        # Find term
                        from apps.academics.models import Term
                        try:
                            term = Term.objects.get(
                                name=data['term_name'],
                                academic_session__school=school
                            )
                        except Term.DoesNotExist:
                            errors.append(f"Row {row_num}: Term '{data['term_name']}' not found")
                            continue
                        
                        # Check if fee record already exists
                        if FeeRecord.objects.filter(
                            student=student,
                            fee_structure=fee_structure,
                            term=term
                        ).exists():
                            errors.append(f"Row {row_num}: Fee record already exists for this student, fee structure, and term")
                            continue
                        
                        # Create fee record
                        fee_record = FeeRecord.objects.create(
                            student=student,
                            fee_structure=fee_structure,
                            term=term,
                            amount_due=data['amount_due'],
                            due_date=data['due_date']
                        )
                        created_fees.append(fee_record)
                        
                    else:
                        errors.append(f"Row {row_num}: {serializer.errors}")
                        
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
        
        return Response({
            'message': f'Successfully imported {len(created_fees)} fee records',
            'created_count': len(created_fees),
            'errors': errors
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsSchoolOwnerOrSuperAdmin])
def export_fees_csv(request):
    """Export fee records to CSV file"""
    user = request.user
    
    if user.is_super_admin:
        fee_records = FeeRecord.objects.all()
    elif user.is_school_owner:
        fee_records = FeeRecord.objects.filter(student__user__school__owner=user)
    else:
        fee_records = FeeRecord.objects.none()
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="fees_export.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Student ID', 'Student Name', 'Fee Structure', 'Term',
        'Amount Due', 'Amount Paid', 'Balance', 'Status', 'Due Date'
    ])
    
    # Write data
    for fee_record in fee_records:
        data = {
            'student_id': fee_record.student.student_id,
            'student_name': fee_record.student.user.get_full_name(),
            'fee_structure_name': fee_record.fee_structure.name,
            'term_name': fee_record.term.name if fee_record.term else '',
            'amount_due': fee_record.amount_due,
            'amount_paid': fee_record.amount_paid,
            'balance': fee_record.balance,
            'status': fee_record.status,
            'due_date': fee_record.due_date
        }
        
        writer.writerow([
            data['student_id'], data['student_name'], data['fee_structure_name'],
            data['term_name'], data['amount_due'], data['amount_paid'],
            data['balance'], data['status'], data['due_date']
        ])
    
    return response


# CSV Template Downloads
@api_view(['GET'])
@permission_classes([IsSchoolOwnerOrSuperAdmin])
def download_student_csv_template(request):
    """Download CSV template for student import"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="student_import_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'first_name', 'last_name', 'email', 'username', 'password',
        'date_of_birth', 'gender', 'address', 'emergency_contact',
        'blood_group', 'medical_conditions', 'guardian_name',
        'guardian_relationship', 'guardian_phone', 'guardian_email',
        'admission_date', 'current_class'
    ])
    
    # Add sample row
    writer.writerow([
        'John', 'Doe', 'john.doe@example.com', 'johndoe', 'password123',
        '2010-01-15', 'male', '123 Main St', '+1234567890',
        'O+', 'None', 'Jane Doe', 'Mother', '+1234567891',
        'jane.doe@example.com', '2023-09-01', 'Grade 5A'
    ])
    
    return response

@api_view(['GET'])
@permission_classes([IsSchoolOwnerOrSuperAdmin])
def download_teacher_csv_template(request):
    """Download CSV template for teacher import"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="teacher_import_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'first_name', 'last_name', 'email', 'username', 'password', 'phone_number'
    ])
    
    # Add sample row
    writer.writerow([
        'Jane', 'Smith', 'jane.smith@example.com', 'janesmith', 'password123', '+1234567890'
    ])
    
    return response

@api_view(['GET'])
@permission_classes([IsSchoolOwnerOrSuperAdmin])
def download_fee_csv_template(request):
    """Download CSV template for fee import"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="fee_import_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'student_id', 'fee_structure_name', 'term_name', 'amount_due', 'due_date'
    ])
    
    # Add sample row
    writer.writerow([
        'SCH2023001', 'Tuition Fee', 'First Term', '50000.00', '2023-10-15'
    ])
    

    return response

@api_view(['GET'])
@permission_classes([IsSchoolOwnerOrSuperAdmin])
def check_import_status(request, task_id):
    """Check the status of an async import task"""
    from celery.result import AsyncResult
    
    task = AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Task is waiting to be processed'
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'result': task.result
        }
    elif task.state == 'FAILURE':
        response = {
            'state': task.state,
            'error': str(task.info)
        }
    else:
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
    
    return Response(response)

