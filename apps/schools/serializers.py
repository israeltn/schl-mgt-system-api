from rest_framework import serializers
from .models import School, SchoolGroup, SMTPSettings

class SchoolGroupSerializer(serializers.ModelSerializer):
    """Serializer for SchoolGroup model"""
    
    class Meta:
        model = SchoolGroup
        fields = ['id', 'name', 'description', 'owner', 'created_at']
        read_only_fields = ['id', 'created_at']

class SMTPSettingsSerializer(serializers.ModelSerializer):
    """Serializer for SMTP settings"""
    
    class Meta:
        model = SMTPSettings
        fields = [
            'id', 'host', 'port', 'use_tls', 'use_ssl',
            'username', 'password', 'from_email', 'from_name',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }

class SchoolSerializer(serializers.ModelSerializer):
    """Serializer for School model"""
    smtp_settings = SMTPSettingsSerializer(read_only=True)
    total_students = serializers.ReadOnlyField()
    total_teachers = serializers.ReadOnlyField()
    total_classes = serializers.ReadOnlyField()
    
    class Meta:
        model = School
        fields = [
            'id', 'name', 'address', 'contact_email', 'contact_number',
            'website', 'logo', 'dashboard_primary_color', 
            'dashboard_secondary_color', 'owner', 'school_group',
            'is_active', 'total_students', 'total_teachers', 
            'total_classes', 'smtp_settings', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class SchoolCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new schools"""
    
    class Meta:
        model = School
        fields = [
            'name', 'address', 'contact_email', 'contact_number',
            'website', 'logo', 'dashboard_primary_color',
            'dashboard_secondary_color', 'school_group'
        ]

class SchoolUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating school information"""
    
    class Meta:
        model = School
        fields = [
            'name', 'address', 'contact_email', 'contact_number',
            'website', 'logo', 'dashboard_primary_color',
            'dashboard_secondary_color'
        ]

class SchoolDashboardSerializer(serializers.ModelSerializer):
    """Serializer for school dashboard data"""
    total_students = serializers.ReadOnlyField()
    total_teachers = serializers.ReadOnlyField()
    total_classes = serializers.ReadOnlyField()
    recent_students = serializers.SerializerMethodField()
    
    class Meta:
        model = School
        fields = [
            'id', 'name', 'total_students', 'total_teachers',
            'total_classes', 'recent_students'
        ]
    
    def get_recent_students(self, obj):
        """Get recently enrolled students"""
        from apps.accounts.serializers import UserSerializer
        recent_students = obj.users.filter(
            role='student', is_active=True
        ).order_by('-created_at')[:5]
        return UserSerializer(recent_students, many=True).data