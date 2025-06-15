from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from apps.accounts.views import IsSchoolOwnerOrSuperAdmin, IsStudent, IsTeacher
from .models import Student, Enrollment, StudentAttendance
from .serializers import (
    StudentSerializer, StudentCreateSerializer, EnrollmentSerializer,
    StudentAttendanceSerializer, BulkAttendanceSerializer,
    StudentDashboardSerializer
)

class StudentListView(generics.ListCreateAPIView):
    """List and create students"""
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StudentCreateSerializer
        return StudentSerializer
    
    def get_queryset(self):
        user = self.request.user
        class_id = self.request.query_params.get('class')
        
        if user.is_super_admin:
            queryset = Student.objects.all()
        elif user.is_school_owner:
            queryset = Student.objects.filter(user__school__owner=user)
        elif user.school:
            queryset = Student.objects.filter(user__school=user.school)
        else:
            queryset = Student.objects.none()
        
        if class_id:
            queryset = queryset.filter(current_class_id=class_id)
        
        return queryset.select_related('user', 'current_class')
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.is_school_owner:
            school = user.owned_schools.first()
            # Set the school for the user
            student = serializer.save()
            student.user.school = school
            student.user.save()

class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete student details"""
    serializer_class = StudentSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Student.objects.all()
        elif user.is_school_owner:
            return Student.objects.filter(user__school__owner=user)
        elif user.school:
            return Student.objects.filter(user__school=user.school)
        return Student.objects.none()

class StudentProfileView(generics.RetrieveUpdateAPIView):
    """Student's own profile view"""
    serializer_class = StudentDashboardSerializer
    permission_classes = [IsStudent]
    
    def get_object(self):
        return self.request.user.student_profile

# Enrollment Views
class EnrollmentListView(generics.ListCreateAPIView):
    """List and create enrollments"""
    serializer_class = EnrollmentSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        student_id = self.request.query_params.get('student')
        session_id = self.request.query_params.get('session')
        
        if user.is_super_admin:
            queryset = Enrollment.objects.all()
        elif user.is_school_owner:
            queryset = Enrollment.objects.filter(
                student__user__school__owner=user
            )
        elif user.school:
            queryset = Enrollment.objects.filter(
                student__user__school=user.school
            )
        else:
            queryset = Enrollment.objects.none()
        
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if session_id:
            queryset = queryset.filter(academic_session_id=session_id)
        
        return queryset.select_related('student', 'class_enrolled', 'academic_session')

class EnrollmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete enrollment"""
    serializer_class = EnrollmentSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Enrollment.objects.all()
        elif user.is_school_owner:
            return Enrollment.objects.filter(
                student__user__school__owner=user
            )
        elif user.school:
            return Enrollment.objects.filter(
                student__user__school=user.school
            )
        return Enrollment.objects.none()

# Attendance Views
class AttendanceListView(generics.ListCreateAPIView):
    """List and create attendance records"""
    serializer_class = StudentAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        date = self.request.query_params.get('date')
        student_id = self.request.query_params.get('student')
        class_id = self.request.query_params.get('class')
        
        if user.is_super_admin:
            queryset = StudentAttendance.objects.all()
        elif user.is_school_owner:
            queryset = StudentAttendance.objects.filter(
                student__user__school__owner=user
            )
        elif user.is_teacher:
            # Teachers can only see attendance for their assigned classes
            assigned_classes = user.teaching_assignments.values_list(
                'class_assigned', flat=True
            )
            queryset = StudentAttendance.objects.filter(
                student__current_class__in=assigned_classes
            )
        elif user.is_student:
            # Students can only see their own attendance
            queryset = StudentAttendance.objects.filter(
                student__user=user
            )
        elif user.school:
            queryset = StudentAttendance.objects.filter(
                student__user__school=user.school
            )
        else:
            queryset = StudentAttendance.objects.none()
        
        if date:
            queryset = queryset.filter(date=date)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if class_id:
            queryset = queryset.filter(student__current_class_id=class_id)
        
        return queryset.select_related('student', 'recorded_by')
    
    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)

class AttendanceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete attendance record"""
    serializer_class = StudentAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return StudentAttendance.objects.all()
        elif user.is_school_owner:
            return StudentAttendance.objects.filter(
                student__user__school__owner=user
            )
        elif user.is_teacher:
            assigned_classes = user.teaching_assignments.values_list(
                'class_assigned', flat=True
            )
            return StudentAttendance.objects.filter(
                student__current_class__in=assigned_classes
            )
        elif user.is_student:
            return StudentAttendance.objects.filter(student__user=user)
        elif user.school:
            return StudentAttendance.objects.filter(
                student__user__school=user.school
            )
        return StudentAttendance.objects.none()

# Bulk operations
@api_view(['POST'])
@permission_classes([IsTeacher])
def bulk_attendance(request):
    """Record attendance for multiple students at once"""
    serializer = BulkAttendanceSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        teacher = request.user
        
        # Verify teacher is assigned to this class
        from apps.academics.models import TeacherAssignment
        if not TeacherAssignment.objects.filter(
            teacher=teacher,
            class_assigned_id=data['class_id'],
            is_active=True
        ).exists():
            return Response(
                {'error': 'You are not assigned to this class'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        attendance_records = []
        with transaction.atomic():
            for record_data in data['attendance_records']:
                student = get_object_or_404(
                    Student,
                    id=record_data['student_id'],
                    current_class_id=data['class_id']
                )
                
                attendance, created = StudentAttendance.objects.update_or_create(
                    student=student,
                    date=data['date'],
                    defaults={
                        'status': record_data['status'],
                        'time_in': record_data.get('time_in'),
                        'time_out': record_data.get('time_out'),
                        'remarks': record_data.get('remarks', ''),
                        'recorded_by': teacher
                    }
                )
                attendance_records.append(attendance)
        
        return Response({
            'message': f'Recorded attendance for {len(attendance_records)} students',
            'records': StudentAttendanceSerializer(attendance_records, many=True).data
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_class_students(request, class_id):
    """Get all students in a specific class"""
    user = request.user
    
    # Check permissions
    if user.is_teacher:
        from apps.academics.models import TeacherAssignment
        if not TeacherAssignment.objects.filter(
            teacher=user,
            class_assigned_id=class_id,
            is_active=True
        ).exists():
            return Response(
                {'error': 'You are not assigned to this class'},
                status=status.HTTP_403_FORBIDDEN
            )
    elif not (user.is_school_owner or user.is_super_admin):
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    students = Student.objects.filter(
        current_class_id=class_id,
        is_active=True
    ).select_related('user')
    
    serializer = StudentSerializer(students, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsStudent])
def student_dashboard(request):
    """Get dashboard data for student"""
    student = request.user.student_profile
    serializer = StudentDashboardSerializer(student)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def attendance_summary(request):
    """Get attendance summary for students"""
    user = request.user
    student_id = request.query_params.get('student')
    month = request.query_params.get('month', timezone.now().month)
    year = request.query_params.get('year', timezone.now().year)
    
    if user.is_student:
        student = user.student_profile
    elif student_id:
        student = get_object_or_404(Student, id=student_id)
        # Check permissions
        if user.is_school_owner and student.user.school not in user.owned_schools.all():
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        elif user.school and student.user.school != user.school:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response({'error': 'Student ID required'}, status=status.HTTP_400_BAD_REQUEST)
    
    from django.db.models import Count, Q
    
    summary = student.attendance_records.filter(
        date__month=month,
        date__year=year
    ).aggregate(
        total_days=Count('id'),
        present_days=Count('id', filter=Q(status='present')),
        absent_days=Count('id', filter=Q(status='absent')),
        late_days=Count('id', filter=Q(status='late')),
        excused_days=Count('id', filter=Q(status='excused'))
    )
    
    # Calculate percentage
    if summary['total_days'] > 0:
        summary['attendance_percentage'] = (
            summary['present_days'] / summary['total_days']
        ) * 100
    else:
        summary['attendance_percentage'] = 0
    
    return Response(summary)