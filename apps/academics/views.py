from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from apps.accounts.views import IsSchoolOwnerOrSuperAdmin, IsTeacher
from .models import AcademicSession, Term, Subject, Class, TeacherAssignment
from .serializers import (
    AcademicSessionSerializer, TermSerializer, SubjectSerializer,
    ClassSerializer, TeacherAssignmentSerializer, TeacherAssignmentCreateSerializer,
    BulkClassCreateSerializer, BulkSubjectCreateSerializer
)

# Academic Session Views
class AcademicSessionListView(generics.ListCreateAPIView):
    """List and create academic sessions"""
    serializer_class = AcademicSessionSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return AcademicSession.objects.all()
        elif user.is_school_owner:
            return AcademicSession.objects.filter(school__owner=user)
        return AcademicSession.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.is_school_owner:
            # Get the first school owned by the user
            school = user.owned_schools.first()
            serializer.save(school=school)
        else:
            serializer.save()

class AcademicSessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete academic session"""
    serializer_class = AcademicSessionSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return AcademicSession.objects.all()
        elif user.is_school_owner:
            return AcademicSession.objects.filter(school__owner=user)
        return AcademicSession.objects.none()

# Term Views
class TermListView(generics.ListCreateAPIView):
    """List and create terms"""
    serializer_class = TermSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        session_id = self.request.query_params.get('session')
        
        if user.is_super_admin:
            queryset = Term.objects.all()
        elif user.is_school_owner:
            queryset = Term.objects.filter(academic_session__school__owner=user)
        else:
            queryset = Term.objects.none()
        
        if session_id:
            queryset = queryset.filter(academic_session_id=session_id)
        
        return queryset

class TermDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete term"""
    serializer_class = TermSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Term.objects.all()
        elif user.is_school_owner:
            return Term.objects.filter(academic_session__school__owner=user)
        return Term.objects.none()

# Subject Views
class SubjectListView(generics.ListCreateAPIView):
    """List and create subjects"""
    serializer_class = SubjectSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Subject.objects.all()
        elif user.is_school_owner:
            return Subject.objects.filter(school__owner=user)
        elif user.school:
            return Subject.objects.filter(school=user.school)
        return Subject.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.is_school_owner:
            school = user.owned_schools.first()
            serializer.save(school=school)
        elif user.school:
            serializer.save(school=user.school)

class SubjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete subject"""
    serializer_class = SubjectSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Subject.objects.all()
        elif user.is_school_owner:
            return Subject.objects.filter(school__owner=user)
        elif user.school:
            return Subject.objects.filter(school=user.school)
        return Subject.objects.none()

# Class Views
class ClassListView(generics.ListCreateAPIView):
    """List and create classes"""
    serializer_class = ClassSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        session_id = self.request.query_params.get('session')
        
        if user.is_super_admin:
            queryset = Class.objects.all()
        elif user.is_school_owner:
            queryset = Class.objects.filter(school__owner=user)
        elif user.school:
            queryset = Class.objects.filter(school=user.school)
        else:
            queryset = Class.objects.none()
        
        if session_id:
            queryset = queryset.filter(academic_session_id=session_id)
        
        return queryset
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.is_school_owner:
            school = user.owned_schools.first()
            serializer.save(school=school)
        elif user.school:
            serializer.save(school=user.school)

class ClassDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete class"""
    serializer_class = ClassSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Class.objects.all()
        elif user.is_school_owner:
            return Class.objects.filter(school__owner=user)
        elif user.school:
            return Class.objects.filter(school=user.school)
        return Class.objects.none()

# Teacher Assignment Views
class TeacherAssignmentListView(generics.ListCreateAPIView):
    """List and create teacher assignments"""
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TeacherAssignmentCreateSerializer
        return TeacherAssignmentSerializer
    
    def get_queryset(self):
        user = self.request.user
        teacher_id = self.request.query_params.get('teacher')
        class_id = self.request.query_params.get('class')
        
        if user.is_super_admin:
            queryset = TeacherAssignment.objects.all()
        elif user.is_school_owner:
            queryset = TeacherAssignment.objects.filter(
                class_assigned__school__owner=user
            )
        elif user.school:
            queryset = TeacherAssignment.objects.filter(
                class_assigned__school=user.school
            )
        else:
            queryset = TeacherAssignment.objects.none()
        
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if class_id:
            queryset = queryset.filter(class_assigned_id=class_id)
        
        return queryset

class TeacherAssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete teacher assignment"""
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return TeacherAssignment.objects.all()
        elif user.is_school_owner:
            return TeacherAssignment.objects.filter(
                class_assigned__school__owner=user
            )
        elif user.school:
            return TeacherAssignment.objects.filter(
                class_assigned__school=user.school
            )
        return TeacherAssignment.objects.none()

# Teacher-specific views
@api_view(['GET'])
@permission_classes([IsTeacher])
def get_teacher_assignments(request):
    """Get assignments for the logged-in teacher"""
    teacher = request.user
    assignments = TeacherAssignment.objects.filter(
        teacher=teacher, is_active=True
    )
    serializer = TeacherAssignmentSerializer(assignments, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsTeacher])
def get_teacher_classes(request):
    """Get classes assigned to the logged-in teacher"""
    teacher = request.user
    assignments = TeacherAssignment.objects.filter(
        teacher=teacher, is_active=True
    ).select_related('class_assigned', 'subject')
    
    classes_data = {}
    for assignment in assignments:
        class_id = assignment.class_assigned.id
        if class_id not in classes_data:
            classes_data[class_id] = {
                'class': ClassSerializer(assignment.class_assigned).data,
                'subjects': []
            }
        classes_data[class_id]['subjects'].append({
            'id': assignment.subject.id,
            'name': assignment.subject.name,
            'code': assignment.subject.code,
            'is_primary': assignment.is_primary_teacher
        })
    
    return Response(list(classes_data.values()))

# Bulk operations
@api_view(['POST'])
@permission_classes([IsSchoolOwnerOrSuperAdmin])
def bulk_create_classes(request):
    """Create multiple classes at once"""
    serializer = BulkClassCreateSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        school = user.owned_schools.first() if user.is_school_owner else None
        
        if not school and not user.is_super_admin:
            return Response(
                {'error': 'School not found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        classes_created = []
        
        with transaction.atomic():
            for level in data['levels']:
                for section in data['sections']:
                    class_name = f"{level}{section}"
                    class_obj = Class.objects.create(
                        name=class_name,
                        level=level,
                        section=section,
                        school=school,
                        academic_session=data['academic_session'],
                        max_students=data['max_students']
                    )
                    classes_created.append(ClassSerializer(class_obj).data)
        
        return Response({
            'message': f'Created {len(classes_created)} classes',
            'classes': classes_created
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsSchoolOwnerOrSuperAdmin])
def bulk_create_subjects(request):
    """Create multiple subjects at once"""
    serializer = BulkSubjectCreateSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        school = user.owned_schools.first() if user.is_school_owner else None
        
        if not school and not user.is_super_admin:
            return Response(
                {'error': 'School not found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        subjects_created = []
        
        with transaction.atomic():
            for subject_data in data['subjects']:
                subject_obj = Subject.objects.create(
                    name=subject_data['name'],
                    code=subject_data.get('code', ''),
                    description=subject_data.get('description', ''),
                    school=school
                )
                subjects_created.append(SubjectSerializer(subject_obj).data)
        
        return Response({
            'message': f'Created {len(subjects_created)} subjects',
            'subjects': subjects_created
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)