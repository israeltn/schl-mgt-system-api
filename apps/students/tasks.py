from celery import shared_task
from django.core.mail import send_mail
from django.db import transaction
import csv
import io
import json
from apps.accounts.models import User
from apps.students.models import Student
from apps.academics.models import Class
from apps.financials.models import FeeRecord, FeeStructure
from apps.academics.models import Term


@shared_task
def process_student_csv_import(file_content, school_id, field_mapping, user_id):
    """Process student CSV import asynchronously"""
    from apps.schools.models import School
    from apps.accounts.models import User as ImportUser
    
    try:
        school = School.objects.get(id=school_id)
        user = ImportUser.objects.get(id=user_id)
        
        # Parse CSV content
        io_string = io.StringIO(file_content)
        reader = csv.DictReader(io_string)
        
        created_students = []
        errors = []
        
        # Default field mapping
        default_mapping = {
            'first_name': 'first_name',
            'last_name': 'last_name',
            'email': 'email',
            'username': 'username',
            'password': 'password',
            'date_of_birth': 'date_of_birth',
            'gender': 'gender',
            'address': 'address',
            'emergency_contact': 'emergency_contact',
            'blood_group': 'blood_group',
            'medical_conditions': 'medical_conditions',
            'guardian_name': 'guardian_name',
            'guardian_relationship': 'guardian_relationship',
            'guardian_phone': 'guardian_phone',
            'guardian_email': 'guardian_email',
            'admission_date': 'admission_date',
            'current_class': 'current_class'
        }
        
        # Merge with custom field mapping
        mapping = {**default_mapping, **field_mapping} if field_mapping else default_mapping
        
        with transaction.atomic():
            for row_num, row in enumerate(reader, 1):
                try:
                    # Map fields according to mapping
                    mapped_data = {}
                    for target_field, source_field in mapping.items():
                        if source_field in row:
                            mapped_data[target_field] = row[source_field].strip() if row[source_field] else ''
                    
                    # Create user
                    user_data = {
                        'username': mapped_data.get('username'),
                        'email': mapped_data.get('email'),
                        'first_name': mapped_data.get('first_name'),
                        'last_name': mapped_data.get('last_name'),
                        'role': 'student',
                        'school': school
                    }
                    
                    # Check if user already exists
                    if User.objects.filter(username=user_data['username']).exists():
                        errors.append(f"Row {row_num}: Username '{user_data['username']}' already exists")
                        continue
                    
                    if User.objects.filter(email=user_data['email']).exists():
                        errors.append(f"Row {row_num}: Email '{user_data['email']}' already exists")
                        continue
                    
                    new_user = User.objects.create_user(**user_data)
                    new_user.set_password(mapped_data.get('password', 'defaultpass123'))
                    new_user.save()
                    
                    # Find class if specified
                    current_class = None
                    if mapped_data.get('current_class'):
                        current_class = Class.objects.filter(
                            name=mapped_data['current_class'],
                            school=school
                        ).first()
                    
                    # Create student
                    student_data = {
                        'user': new_user,
                        'date_of_birth': mapped_data.get('date_of_birth'),
                        'gender': mapped_data.get('gender'),
                        'address': mapped_data.get('address'),
                        'emergency_contact': mapped_data.get('emergency_contact'),
                        'blood_group': mapped_data.get('blood_group', ''),
                        'medical_conditions': mapped_data.get('medical_conditions', ''),
                        'guardian_name': mapped_data.get('guardian_name', ''),
                        'guardian_relationship': mapped_data.get('guardian_relationship', ''),
                        'guardian_phone': mapped_data.get('guardian_phone', ''),
                        'guardian_email': mapped_data.get('guardian_email', ''),
                        'admission_date': mapped_data.get('admission_date'),
                        'current_class': current_class
                    }
                    
                    student = Student.objects.create(**student_data)
                    created_students.append(student)
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
        
        # Send completion email
        subject = f"CSV Import Complete - {len(created_students)} students imported"
        message = f"""
        Your student CSV import has been completed.
        
        Summary:
        - Total students imported: {len(created_students)}
        - Errors encountered: {len(errors)}
        
        {"Errors:" + chr(10).join(errors) if errors else "No errors encountered."}
        """
        
        send_mail(
            subject,
            message,
            'noreply@school.com',
            [user.email],
            fail_silently=True
        )
        
        return {
            'success': True,
            'created_count': len(created_students),
            'errors': errors
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def process_teacher_csv_import(file_content, school_id, field_mapping, user_id):
    """Process teacher CSV import asynchronously"""
    from apps.schools.models import School
    from apps.accounts.models import User as ImportUser
    
    try:
        school = School.objects.get(id=school_id)
        user = ImportUser.objects.get(id=user_id)
        
        # Parse CSV content
        io_string = io.StringIO(file_content)
        reader = csv.DictReader(io_string)
        
        created_teachers = []
        errors = []
        
        # Default field mapping
        default_mapping = {
            'first_name': 'first_name',
            'last_name': 'last_name',
            'email': 'email',
            'username': 'username',
            'password': 'password',
            'phone_number': 'phone_number'
        }
        
        # Merge with custom field mapping
        mapping = {**default_mapping, **field_mapping} if field_mapping else default_mapping
        
        with transaction.atomic():
            for row_num, row in enumerate(reader, 1):
                try:
                    # Map fields according to mapping
                    mapped_data = {}
                    for target_field, source_field in mapping.items():
                        if source_field in row:
                            mapped_data[target_field] = row[source_field].strip() if row[source_field] else ''
                    
                    # Check if user already exists
                    if User.objects.filter(username=mapped_data.get('username')).exists():
                        errors.append(f"Row {row_num}: Username '{mapped_data.get('username')}' already exists")
                        continue
                    
                    if User.objects.filter(email=mapped_data.get('email')).exists():
                        errors.append(f"Row {row_num}: Email '{mapped_data.get('email')}' already exists")
                        continue
                    
                    # Create teacher user
                    user_data = {
                        'username': mapped_data.get('username'),
                        'email': mapped_data.get('email'),
                        'first_name': mapped_data.get('first_name'),
                        'last_name': mapped_data.get('last_name'),
                        'phone_number': mapped_data.get('phone_number', ''),
                        'role': 'teacher',
                        'school': school
                    }
                    
                    teacher = User.objects.create_user(**user_data)
                    teacher.set_password(mapped_data.get('password', 'defaultpass123'))
                    teacher.save()
                    created_teachers.append(teacher)
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
        
        # Send completion email
        subject = f"CSV Import Complete - {len(created_teachers)} teachers imported"
        message = f"""
        Your teacher CSV import has been completed.
        
        Summary:
        - Total teachers imported: {len(created_teachers)}
        - Errors encountered: {len(errors)}
        
        {"Errors:" + chr(10).join(errors) if errors else "No errors encountered."}
        """
        
        send_mail(
            subject,
            message,
            'noreply@school.com',
            [user.email],
            fail_silently=True
        )
        
        return {
            'success': True,
            'created_count': len(created_teachers),
            'errors': errors
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def process_fee_csv_import(file_content, school_id, field_mapping, user_id):
    """Process fee CSV import asynchronously"""
    from apps.schools.models import School
    from apps.accounts.models import User as ImportUser
    
    try:
        school = School.objects.get(id=school_id)
        user = ImportUser.objects.get(id=user_id)
        
        # Parse CSV content
        io_string = io.StringIO(file_content)
        reader = csv.DictReader(io_string)
        
        created_fees = []
        errors = []
        
        # Default field mapping
        default_mapping = {
            'student_id': 'student_id',
            'fee_structure_name': 'fee_structure_name',
            'term_name': 'term_name',
            'amount_due': 'amount_due',
            'due_date': 'due_date'
        }
        
        # Merge with custom field mapping
        mapping = {**default_mapping, **field_mapping} if field_mapping else default_mapping
        
        with transaction.atomic():
            for row_num, row in enumerate(reader, 1):
                try:
                    # Map fields according to mapping
                    mapped_data = {}
                    for target_field, source_field in mapping.items():
                        if source_field in row:
                            mapped_data[target_field] = row[source_field].strip() if row[source_field] else ''
                    
                    # Find student
                    try:
                        student = Student.objects.get(
                            student_id=mapped_data.get('student_id'),
                            user__school=school
                        )
                    except Student.DoesNotExist:
                        errors.append(f"Row {row_num}: Student with ID '{mapped_data.get('student_id')}' not found")
                        continue
                    
                    # Find fee structure
                    try:
                        fee_structure = FeeStructure.objects.get(
                            name=mapped_data.get('fee_structure_name'),
                            school=school
                        )
                    except FeeStructure.DoesNotExist:
                        errors.append(f"Row {row_num}: Fee structure '{mapped_data.get('fee_structure_name')}' not found")
                        continue
                    
                    # Find term
                    try:
                        term = Term.objects.get(
                            name=mapped_data.get('term_name'),
                            academic_session__school=school
                        )
                    except Term.DoesNotExist:
                        errors.append(f"Row {row_num}: Term '{mapped_data.get('term_name')}' not found")
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
                        amount_due=mapped_data.get('amount_due'),
                        due_date=mapped_data.get('due_date')
                    )
                    created_fees.append(fee_record)
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
        
        # Send completion email
        subject = f"CSV Import Complete - {len(created_fees)} fee records imported"
        message = f"""
        Your fee CSV import has been completed.
        
        Summary:
        - Total fee records imported: {len(created_fees)}
        - Errors encountered: {len(errors)}
        
        {"Errors:" + chr(10).join(errors) if errors else "No errors encountered."}
        """
        
        send_mail(
            subject,
            message,
            'noreply@school.com',
            [user.email],
            fail_silently=True
        )
        
        return {
            'success': True,
            'created_count': len(created_fees),
            'errors': errors
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }