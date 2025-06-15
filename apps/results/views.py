from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Avg, Max, Min, Count
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
            if user.student_profile.fee_status == 'cleared':
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
            if user.student_profile.fee_status == 'cleared':
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
        return Response(
            {'message': 'Results updated successfully', 'results': ResultSerializer(results_created, many=True).data},
            status=status.HTTP_201_CREATED
        )