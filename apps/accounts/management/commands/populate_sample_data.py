from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta
from apps.accounts.models import User
from apps.schools.models import School, SchoolGroup
from apps.academics.models import AcademicSession, Term, Subject, Class, TeacherAssignment
from apps.students.models import Student
from apps.financials.models import FeeStructure


class Command(BaseCommand):
    help = 'Populate database with sample data for testing'

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write('Creating sample data...')
            
            # Create Super Admin
            super_admin = User.objects.create_superuser(
                username='superadmin',
                email='superadmin@school.com',
                password='admin123',
                first_name='Super',
                last_name='Admin',
                role='super_admin'
            )
            self.stdout.write(self.style.SUCCESS('✓ Created super admin'))
            
            # Create School Owner
            school_owner = User.objects.create_user(
                username='schoolowner',
                email='owner@school.com',
                password='owner123',
                first_name='John',
                last_name='Owner',
                role='school_owner'
            )
            
            # Create School
            school = School.objects.create(
                name='Excellence Academy',
                address='123 Education Street, Learning City',
                contact_email='info@excellenceacademy.com',
                contact_number='+1234567890',
                owner=school_owner,
                dashboard_primary_color='#3B82F6',
                dashboard_secondary_color='#1E40AF'
            )
            self.stdout.write(self.style.SUCCESS('✓ Created school'))
            
            # Create Academic Session
            current_year = timezone.now().year
            session = AcademicSession.objects.create(
                name=f'{current_year}/{current_year + 1}',
                start_date=date(current_year, 9, 1),
                end_date=date(current_year + 1, 7, 31),
                is_active=True,
                school=school
            )
            
            # Create Terms
            terms = [
                Term.objects.create(
                    name='First Term',
                    academic_session=session,
                    start_date=date(current_year, 9, 1),
                    end_date=date(current_year, 12, 20),
                    is_active=True
                ),
                Term.objects.create(
                    name='Second Term',
                    academic_session=session,
                    start_date=date(current_year + 1, 1, 10),
                    end_date=date(current_year + 1, 4, 10),
                    is_active=False
                ),
                Term.objects.create(
                    name='Third Term',
                    academic_session=session,
                    start_date=date(current_year + 1, 4, 25),
                    end_date=date(current_year + 1, 7, 31),
                    is_active=False
                )
            ]
            self.stdout.write(self.style.SUCCESS('✓ Created academic session and terms'))
            
            # Create Subjects
            subjects = []
            subject_names = [
                ('Mathematics', 'MATH'),
                ('English Language', 'ENG'),
                ('Science', 'SCI'),
                ('Social Studies', 'SOC'),
                ('Computer Science', 'COMP'),
                ('Physical Education', 'PE'),
                ('Art', 'ART'),
                ('Music', 'MUS')
            ]
            
            for name, code in subject_names:
                subjects.append(Subject.objects.create(
                    name=name,
                    code=code,
                    school=school
                ))
            self.stdout.write(self.style.SUCCESS('✓ Created subjects'))
            
            # Create Classes
            classes = []
            class_levels = [
                ('Grade 1', 'Primary 1', 'A'),
                ('Grade 1', 'Primary 1', 'B'),
                ('Grade 2', 'Primary 2', 'A'),
                ('Grade 2', 'Primary 2', 'B'),
                ('Grade 3', 'Primary 3', 'A'),
                ('Grade 4', 'Primary 4', 'A'),
                ('Grade 5', 'Primary 5', 'A'),
                ('Grade 6', 'Primary 6', 'A')
            ]
            
            for name, level, section in class_levels:
                classes.append(Class.objects.create(
                    name=f'{name}{section}',
                    level=level,
                    section=section,
                    school=school,
                    academic_session=session,
                    max_students=30
                ))
            self.stdout.write(self.style.SUCCESS('✓ Created classes'))
            
            # Create Teachers
            teachers = []
            teacher_data = [
                ('teacher1', 'Sarah', 'Johnson', 'sarah.johnson@school.com'),
                ('teacher2', 'Michael', 'Brown', 'michael.brown@school.com'),
                ('teacher3', 'Emily', 'Davis', 'emily.davis@school.com'),
                ('teacher4', 'David', 'Wilson', 'david.wilson@school.com'),
                ('teacher5', 'Jessica', 'Martinez', 'jessica.martinez@school.com')
            ]
            
            for username, first, last, email in teacher_data:
                teacher = User.objects.create_user(
                    username=username,
                    email=email,
                    password='teacher123',
                    first_name=first,
                    last_name=last,
                    role='teacher',
                    school=school
                )
                teachers.append(teacher)
            
            # Assign class teachers
            for i, class_obj in enumerate(classes[:5]):
                class_obj.class_teacher = teachers[i % len(teachers)]
                class_obj.save()
            
            self.stdout.write(self.style.SUCCESS('✓ Created teachers'))
            
            # Create Teacher Assignments
            for class_obj in classes:
                # Assign 3-4 subjects to each class
                assigned_subjects = subjects[:4] if 'Primary 1' in class_obj.level else subjects[:6]
                for i, subject in enumerate(assigned_subjects):
                    TeacherAssignment.objects.create(
                        teacher=teachers[i % len(teachers)],
                        class_assigned=class_obj,
                        subject=subject,
                        academic_session=session,
                        is_primary_teacher=True
                    )
            self.stdout.write(self.style.SUCCESS('✓ Created teacher assignments'))
            
            # Create Students
            student_count = 0
            for class_obj in classes:
                # Create 15-20 students per class
                for i in range(15):
                    student_count += 1
                    user = User.objects.create_user(
                        username=f'student{student_count}',
                        email=f'student{student_count}@school.com',
                        password='student123',
                        first_name=f'Student{student_count}',
                        last_name=f'LastName{student_count}',
                        role='student',
                        school=school
                    )
                    
                    Student.objects.create(
                        user=user,
                        date_of_birth=date(2010, 1, 1) + timedelta(days=student_count * 30),
                        gender='male' if student_count % 2 == 0 else 'female',
                        address=f'{student_count} Student Street',
                        emergency_contact='+1234567890',
                        guardian_name=f'Guardian of Student{student_count}',
                        guardian_relationship='Parent',
                        guardian_phone='+1234567890',
                        guardian_email=f'guardian{student_count}@email.com',
                        admission_date=date(current_year, 9, 1),
                        current_class=class_obj
                    )
            self.stdout.write(self.style.SUCCESS(f'✓ Created {student_count} students'))
            
            # Create Fee Structures
            fee_structures = [
                ('Tuition Fee', 50000, 'termly', True),
                ('Development Levy', 10000, 'annual', True),
                ('Sports Fee', 5000, 'termly', False),
                ('Lab Fee', 3000, 'termly', False),
                ('Library Fee', 2000, 'annual', True)
            ]
            
            for name, amount, frequency, mandatory in fee_structures:
                FeeStructure.objects.create(
                    school=school,
                    academic_session=session,
                    name=name,
                    amount=amount,
                    payment_frequency=frequency,
                    is_mandatory=mandatory
                )
            self.stdout.write(self.style.SUCCESS('✓ Created fee structures'))
            
            # Create Office Account
            User.objects.create_user(
                username='office',
                email='office@school.com',
                password='office123',
                first_name='Office',
                last_name='Manager',
                role='office_account',
                school=school
            )
            self.stdout.write(self.style.SUCCESS('✓ Created office account'))
            
            # Create Parent
            parent = User.objects.create_user(
                username='parent1',
                email='parent1@email.com',
                password='parent123',
                first_name='Parent',
                last_name='One',
                role='parent',
                school=school
            )
            
            # Link first 3 students to this parent
            students_to_link = Student.objects.filter(user__school=school)[:3]
            for student in students_to_link:
                student.parent = parent
                student.save()
            self.stdout.write(self.style.SUCCESS('✓ Created parent account'))
            
            self.stdout.write(self.style.SUCCESS('\n✅ Sample data created successfully!'))
            self.stdout.write('\nLogin credentials:')
            self.stdout.write('- Super Admin: superadmin / admin123')
            self.stdout.write('- School Owner: schoolowner / owner123')
            self.stdout.write('- Teacher: teacher1 / teacher123')
            self.stdout.write('- Student: student1 / student123')
            self.stdout.write('- Parent: parent1 / parent123')
            self.stdout.write('- Office: office / office123')