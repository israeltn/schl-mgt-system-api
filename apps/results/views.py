from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Avg, Max, Min, Count, Q
from django.utils import timezone
from apps.accounts.views import IsSchoolOwnerOrSuperAdmin, IsTeacher, IsStudent
from .models import Result, TermResult, ResultTemplate
from .serializers import (
    ResultSerializer, ResultInputSerializer, BulkResultInputSerializer,
    TermResultSerializer, StudentTermResultSerializer, ResultTemplateSerializer,
    ClassResultSummarySerializer, SubjectPerformanceSerializer
)

class ResultListView(generics.ListCreateAPIView):
    """List and create individual subject results"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ResultInputSerializer
        return ResultSerializer
    
    def get_queryset(self):
        user = self.request.user
        student_id = self.request.query_params.get('student')
        term_id = self.request.query_params.get('term')
        subject_id = self.request.query_params.get('subject')
        
        if user.is_super_admin:
            queryset = Result.objects.all()
        elif user.is_school_owner:
            queryset = Result.objects.filter(
                student__user__school__owner=user
            )
        elif user.is_teacher:
            # Teachers can only see results for subjects they teach
            queryset = Result.objects.filter(teacher=user)
        elif user.is_student:
            # Students can only see their own results if fees are paid
            if hasattr(user, 'student_profile') and user.student_profile.fee_status == 'cleared':
                queryset = Result.objects.filter(student__user=user)
            else:
                queryset = Result.objects.none()
        elif user.school:
            queryset = Result.objects.filter(student__user__school=user.school)
        else:
            queryset = Result.objects.none()
        
        # Apply filters
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if term_id:
            queryset = queryset.filter(term_id=term_id)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        
        return queryset.select_related('student', 'subject', 'term', 'teacher')
    
    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)

class ResultDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete individual result"""
    serializer_class = ResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ResultInputSerializer
        return ResultSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Result.objects.all()
        elif user.is_school_owner:
            return Result.objects.filter(student__user__school__owner=user)
        elif user.is_teacher:
            return Result.objects.filter(teacher=user)
        elif user.is_student:
            if hasattr(user, 'student_profile') and user.student_profile.fee_status == 'cleared':
                return Result.objects.filter(student__user=user)
            else:
                return Result.objects.none()
        elif user.school:
            return Result.objects.filter(student__user__school=user.school)
        return Result.objects.none()

class TermResultListView(generics.ListCreateAPIView):
    """List and create term results"""
    serializer_class = TermResultSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        student_id = self.request.query_params.get('student')
        term_id = self.request.query_params.get('term')
        class_id = self.request.query_params.get('class')
        
        if user.is_super_admin:
            queryset = TermResult.objects.all()
        elif user.is_school_owner:
            queryset = TermResult.objects.filter(
                student__user__school__owner=user
            )
        elif user.school:
            queryset = TermResult.objects.filter(
                student__user__school=user.school
            )
        else:
            queryset = TermResult.objects.none()
        
        # Apply filters
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if term_id:
            queryset = queryset.filter(term_id=term_id)
        if class_id:
            queryset = queryset.filter(class_for_term_id=class_id)
        
        return queryset.select_related('student', 'term', 'class_for_term')

class TermResultDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete term result"""
    serializer_class = TermResultSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return TermResult.objects.all()
        elif user.is_school_owner:
            return TermResult.objects.filter(student__user__school__owner=user)
        elif user.school:
            return TermResult.objects.filter(student__user__school=user.school)
        return TermResult.objects.none()

# Student-specific views
@api_view(['GET'])
@permission_classes([IsStudent])
def student_results(request):
    """Get results for the logged-in student"""
    student = request.user.student_profile
    
    # Check fee status
    if student.fee_status != 'cleared':
        return Response({
            'message': 'Results not available. Please clear your fees to view results.',
            'fee_status': student.fee_status
        }, status=status.HTTP_403_FORBIDDEN)
    
    term_results = student.term_results.filter(is_published=True)
    serializer = StudentTermResultSerializer(term_results, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsStudent])
def student_term_result(request, term_id):
    """Get specific term result for student"""
    student = request.user.student_profile
    
    # Check fee status
    if student.fee_status != 'cleared':
        return Response({
            'message': 'Results not available. Please clear your fees.',
            'fee_status': student.fee_status
        }, status=status.HTTP_403_FORBIDDEN)
    
    term_result = get_object_or_404(
        TermResult,
        student=student,
        term_id=term_id,
        is_published=True
    )
    
    serializer = StudentTermResultSerializer(term_result)
    return Response(serializer.data)

# Teacher-specific views
@api_view(['POST'])
@permission_classes([IsTeacher])
def bulk_result_input(request):
    """Bulk input of results by teachers"""
    serializer = BulkResultInputSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        teacher = request.user
        
        # Verify teacher is assigned to this class and subject
        from apps.academics.models import TeacherAssignment
        if not TeacherAssignment.objects.filter(
            teacher=teacher,
            class_assigned_id=data['class_id'],
            subject_id=data['subject_id'],
            is_active=True
        ).exists():
            return Response(
                {'error': 'You are not assigned to teach this subject in this class'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        results_created = []
        with transaction.atomic():
            for result_data in data['results']:
                student_id = result_data['student_id']
                result, created = Result.objects.update_or_create(
                    student_id=student_id,
                    subject_id=data['subject_id'],
                    term_id=data['term_id'],
                    defaults={
                        'class_for_term_id': data['class_id'],
                        'first_ca': result_data.get('first_ca'),
                        'second_ca': result_data.get('second_ca'),
                        'exam_marks': result_data.get('exam_marks'),
                        'remarks': result_data.get('remarks', ''),
                        'teacher': teacher
                    }
                )
                results_created.append(result)
        
        return Response({
            'message': 'Results updated successfully',
            'results': ResultSerializer(results_created, many=True).data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Admin operations
@api_view(['POST'])
@permission_classes([IsSchoolOwnerOrSuperAdmin])
def generate_term_results(request):
    """Generate term results for students"""
    term_id = request.data.get('term_id')
    class_id = request.data.get('class_id')
    
    if not term_id:
        return Response({'error': 'term_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
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
    
    results_generated = []
    with transaction.atomic():
        for student in students:
            # Check if term result already exists
            term_result, created = TermResult.objects.get_or_create(
                student=student,
                term=term,
                defaults={
                    'class_for_term': student.current_class
                }
            )
            
            if created or not term_result.is_published:
                # Calculate results
                term_result.calculate_results()
                results_generated.append(term_result)
        
        # Calculate positions for all students in each class
        for term_result in results_generated:
            term_result.calculate_position()
    
    return Response({
        'message': f'Generated term results for {len(results_generated)} students',
        'results_count': len(results_generated)
    })

@api_view(['POST'])
@permission_classes([IsSchoolOwnerOrSuperAdmin])
def publish_results(request):
    """Publish term results"""
    term_id = request.data.get('term_id')
    class_id = request.data.get('class_id')
    
    if not term_id:
        return Response({'error': 'term_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get term results to publish
    term_results = TermResult.objects.filter(term_id=term_id, is_published=False)
    
    if class_id:
        term_results = term_results.filter(class_for_term_id=class_id)
    
    user = request.user
    if user.is_school_owner:
        term_results = term_results.filter(student__user__school__owner=user)
    
    published_count = 0
    with transaction.atomic():
        for term_result in term_results:
            term_result.is_published = True
            term_result.published_at = timezone.now()
            term_result.save()
            published_count += 1
            
            # Queue email notification
            from celery import current_app
            if hasattr(current_app, 'send_task'):
                current_app.send_task(
                    'apps.results.tasks.send_result_notification',
                    args=[term_result.id]
                )
    
    return Response({
        'message': f'Published {published_count} term results',
        'published_count': published_count
    })

# Analytics and reports
@api_view(['GET'])
@permission_classes([IsSchoolOwnerOrSuperAdmin])
def class_result_summary(request):
    """Get class result summary"""
    user = request.user
    term_id = request.query_params.get('term')
    class_id = request.query_params.get('class')
    
    if not term_id or not class_id:
        return Response(
            {'error': 'term and class parameters are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Build queryset
    term_results = TermResult.objects.filter(
        term_id=term_id,
        class_for_term_id=class_id
    )
    
    if user.is_school_owner:
        term_results = term_results.filter(student__user__school__owner=user)
    
    # Calculate summary
    summary_data = term_results.aggregate(
        total_students=Count('id'),
        results_published=Count('id', filter=Q(is_published=True)),
        average_class_score=Avg('average_score'),
        highest_score=Max('average_score'),
        lowest_score=Min('average_score')
    )
    
    # Calculate pass rate (assuming 50% is pass)
    pass_count = term_results.filter(average_score__gte=50).count()
    total_count = summary_data['total_students']
    pass_rate = (pass_count / total_count * 100) if total_count > 0 else 0
    
    summary_data['pass_rate'] = round(pass_rate, 2)
    
    # Get class and term names
    from apps.academics.models import Class, Term
    class_obj = get_object_or_404(Class, id=class_id)
    term_obj = get_object_or_404(Term, id=term_id)
    
    summary_data['class_name'] = class_obj.name
    summary_data['term_name'] = term_obj.name
    
    serializer = ClassResultSummarySerializer(summary_data)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsSchoolOwnerOrSuperAdmin])
def subject_performance(request):
    """Get subject performance analysis"""
    user = request.user
    term_id = request.query_params.get('term')
    subject_id = request.query_params.get('subject')
    
    if not term_id or not subject_id:
        return Response(
            {'error': 'term and subject parameters are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Build queryset
    results = Result.objects.filter(
        term_id=term_id,
        subject_id=subject_id
    )
    
    if user.is_school_owner:
        results = results.filter(student__user__school__owner=user)
    
    # Calculate performance metrics
    performance_data = results.aggregate(
        total_students=Count('id'),
        average_score=Avg('average_score'),
        highest_score=Max('average_score'),
        lowest_score=Min('average_score')
    )
    
    # Grade distribution
    grade_distribution = {
        'A': results.filter(average_score__gte=80).count(),
        'B': results.filter(average_score__gte=70, average_score__lt=80).count(),
        'C': results.filter(average_score__gte=60, average_score__lt=70).count(),
        'D': results.filter(average_score__gte=50, average_score__lt=60).count(),
        'E': results.filter(average_score__gte=40, average_score__lt=50).count(),
        'F': results.filter(average_score__lt=40).count(),
    }
    
    performance_data['grade_distribution'] = grade_distribution
    
    # Get subject name
    from apps.academics.models import Subject
    subject_obj = get_object_or_404(Subject, id=subject_id)
    performance_data['subject_name'] = subject_obj.name
    
    serializer = SubjectPerformanceSerializer(performance_data)
    return Response(serializer.data)

# Result Template
class ResultTemplateView(generics.RetrieveUpdateAPIView):
    """Get and update result template"""
    serializer_class = ResultTemplateSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_object(self):
        user = self.request.user
        school_id = self.kwargs.get('school_id')
        
        if school_id:
            from apps.schools.models import School
            if user.is_super_admin:
                school = get_object_or_404(School, pk=school_id)
            elif user.is_school_owner:
                school = get_object_or_404(School, pk=school_id, owner=user)
            else:
                raise permissions.PermissionDenied()
        else:
            if user.is_school_owner:
                school = user.owned_schools.first()
            else:
                school = user.school
        
        template, created = ResultTemplate.objects.get_or_create(school=school)
        return template