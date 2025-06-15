from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User
from .serializers import (
    UserSerializer, UserCreateSerializer, LoginSerializer,
    UserProfileUpdateSerializer, ChangePasswordSerializer
)

class LoginView(generics.GenericAPIView):
    """Handle user login and return JWT tokens"""
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })

class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile"""
    serializer_class = UserProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserSerializer
        return UserProfileUpdateSerializer

class ChangePasswordView(generics.GenericAPIView):
    """Change user password"""
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Password changed successfully'})

# Permission classes for role-based access
class IsSuperAdmin(permissions.BasePermission):
    """Permission class for Super Admin only"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_super_admin

class IsSchoolOwner(permissions.BasePermission):
    """Permission class for School Owner only"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_school_owner

class IsTeacher(permissions.BasePermission):
    """Permission class for Teacher only"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_teacher

class IsStudent(permissions.BasePermission):
    """Permission class for Student only"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_student

class IsOfficeAccount(permissions.BasePermission):
    """Permission class for Office Account only"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_office_account

class IsSchoolOwnerOrSuperAdmin(permissions.BasePermission):
    """Permission class for School Owner or Super Admin"""
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                (request.user.is_school_owner or request.user.is_super_admin))

# User Management Views (for Super Admin and School Owners)
class UserCreateView(generics.CreateAPIView):
    """Create new users (Super Admin can create School Owners, School Owners can create others)"""
    serializer_class = UserCreateSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.is_school_owner:
            # School owners can only create users for their school
            serializer.save(school=user.school)
        else:
            # Super admin can create any user
            serializer.save()

class UserListView(generics.ListAPIView):
    """List users based on role permissions"""
    serializer_class = UserSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return User.objects.all()
        elif user.is_school_owner:
            return User.objects.filter(school=user.school)
        return User.objects.none()

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete user details"""
    serializer_class = UserSerializer
    permission_classes = [IsSchoolOwnerOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return User.objects.all()
        elif user.is_school_owner:
            return User.objects.filter(school=user.school)
        return User.objects.none()