from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.accounts.views import IsSuperAdmin, IsSchoolOwner, IsSchoolOwnerOrSuperAdmin
from .models import School, SchoolGroup, SMTPSettings
from .serializers import (
    SchoolSerializer, SchoolCreateSerializer, SchoolUpdateSerializer,
    SchoolGroupSerializer, SMTPSettingsSerializer, SchoolDashboardSerializer
)

class SchoolListView(generics.ListCreateAPIView):
    """List and create schools"""
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SchoolCreateSerializer
        return SchoolSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return School.objects.all()
        elif user.is_school_owner:
            return School.objects.filter(owner=user)
        return School.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.is_school_owner:
            serializer.save(owner=user)
        else:
            serializer.save()

class SchoolDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete school details"""
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SchoolUpdateSerializer
        return SchoolSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return School.objects.all()
        elif user.is_school_owner:
            return School.objects.filter(owner=user)
        return School.objects.none()

class SchoolDashboardView(generics.RetrieveAPIView):
    """Get school dashboard data"""
    serializer_class = SchoolDashboardSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_object(self):
        user = self.request.user
        school_id = self.kwargs.get('pk')
        
        if user.is_super_admin:
            return get_object_or_404(School, pk=school_id)
        elif user.is_school_owner:
            return get_object_or_404(School, pk=school_id, owner=user)
        
        # For other roles, get their associated school
        return user.school

# SMTP Settings Views
class SMTPSettingsView(generics.RetrieveUpdateAPIView):
    """Get and update SMTP settings for a school"""
    serializer_class = SMTPSettingsSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_object(self):
        school_id = self.kwargs['school_id']
        user = self.request.user
        
        if user.is_super_admin:
            school = get_object_or_404(School, pk=school_id)
        elif user.is_school_owner:
            school = get_object_or_404(School, pk=school_id, owner=user)
        else:
            raise permissions.PermissionDenied()
        
        smtp_settings, created = SMTPSettings.objects.get_or_create(school=school)
        return smtp_settings

class SMTPSettingsCreateView(generics.CreateAPIView):
    """Create SMTP settings for a school"""
    serializer_class = SMTPSettingsSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def perform_create(self, serializer):
        school_id = self.kwargs['school_id']
        user = self.request.user
        
        if user.is_super_admin:
            school = get_object_or_404(School, pk=school_id)
        elif user.is_school_owner:
            school = get_object_or_404(School, pk=school_id, owner=user)
        else:
            raise permissions.PermissionDenied()
        
        serializer.save(school=school)

# School Group Views
class SchoolGroupListView(generics.ListCreateAPIView):
    """List and create school groups"""
    serializer_class = SchoolGroupSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return SchoolGroup.objects.all()
        elif user.is_school_owner:
            return SchoolGroup.objects.filter(owner=user)
        return SchoolGroup.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.is_school_owner:
            serializer.save(owner=user)
        else:
            serializer.save()

class SchoolGroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete school group details"""
    serializer_class = SchoolGroupSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return SchoolGroup.objects.all()
        elif user.is_school_owner:
            return SchoolGroup.objects.filter(owner=user)
        return SchoolGroup.objects.none()

# Dashboard Views for different roles
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_dashboard(request):
    """Get dashboard data based on user role"""
    user = request.user
    
    if user.is_super_admin:
        # Super admin sees all schools summary
        schools = School.objects.all()
        total_schools = schools.count()
        total_students = sum(school.total_students for school in schools)
        total_teachers = sum(school.total_teachers for school in schools)
        
        return Response({
            'role': 'super_admin',
            'total_schools': total_schools,
            'total_students': total_students,
            'total_teachers': total_teachers,
            'recent_schools': SchoolSerializer(schools.order_by('-created_at')[:5], many=True).data
        })
    
    elif user.is_school_owner:
        # School owner sees their schools
        schools = School.objects.filter(owner=user)
        total_schools = schools.count()
        total_students = sum(school.total_students for school in schools)
        total_teachers = sum(school.total_teachers for school in schools)
        
        return Response({
            'role': 'school_owner',
            'total_schools': total_schools,
            'total_students': total_students,
            'total_teachers': total_teachers,
            'schools': SchoolSerializer(schools, many=True).data
        })
    
    elif user.school:
        # Other roles see their school info
        school = user.school
        return Response({
            'role': user.role,
            'school': SchoolDashboardSerializer(school).data
        })
    
    else:
        return Response({
            'role': user.role,
            'message': 'No school assigned'
        })