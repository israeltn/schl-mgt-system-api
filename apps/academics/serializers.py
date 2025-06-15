from rest_framework import serializers
from .models import AcademicSession, Term, Subject, Class, TeacherAssignment

class AcademicSessionSerializer(serializers.ModelSerializer):
    """Serializer for AcademicSession model"""
    
    class Meta:
        model = AcademicSession
        fields = [
            'id', 'name', 'start_date', 'end_date', 'is_active',
            'school', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class TermSerializer(serializers.ModelSerializer):
    """Serializer for Term model"""
    academic_session_name = serializers.CharField(source='academic_session.name', read_only=True)
    
    class Meta:
        model = Term
        fields = [
            'id', 'name', 'academic_session', 'academic_session_name',
            'start_date', 'end_date', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class SubjectSerializer(serializers.ModelSerializer):
    """Serializer for Subject model"""
    
    class Meta:
        model = Subject
        fields = [
            'id', 'name', 'code', 'description', 'school',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class ClassSerializer(serializers.ModelSerializer):
    """Serializer for Class model"""
    academic_session_name = serializers.CharField(source='academic_session.name', read_only=True)
    class_teacher_name = serializers.CharField(source='class_teacher.get_full_name', read_only=True)
    current_students_count = serializers.ReadOnlyField()
    available_slots = serializers.ReadOnlyField()
    
    class Meta:
        model = Class
        fields = [
            'id', 'name', 'level', 'section', 'school', 'academic_session',
            'academic_session_name', 'max_students', 'class_teacher',
            'class_teacher_name', 'current_students_count', 'available_slots',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class TeacherAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for TeacherAssignment model"""
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    class_name = serializers.CharField(source='class_assigned.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    academic_session_name = serializers.CharField(source='academic_session.name', read_only=True)
    
    class Meta:
        model = TeacherAssignment
        fields = [
            'id', 'teacher', 'teacher_name', 'class_assigned', 'class_name',
            'subject', 'subject_name', 'academic_session', 'academic_session_name',
            'is_primary_teacher', 'is_active', 'assigned_at'
        ]
        read_only_fields = ['id', 'assigned_at']

class TeacherAssignmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating teacher assignments"""
    
    class Meta:
        model = TeacherAssignment
        fields = [
            'teacher', 'class_assigned', 'subject', 'academic_session',
            'is_primary_teacher'
        ]
    
    def validate(self, data):
        """Validate that teacher, class, and subject belong to the same school"""
        teacher = data.get('teacher')
        class_assigned = data.get('class_assigned')
        subject = data.get('subject')
        
        if teacher.school != class_assigned.school:
            raise serializers.ValidationError(
                "Teacher must belong to the same school as the class."
            )
        
        if subject.school != class_assigned.school:
            raise serializers.ValidationError(
                "Subject must belong to the same school as the class."
            )
        
        return data

# Create serializers for bulk operations
class BulkClassCreateSerializer(serializers.Serializer):
    """Serializer for creating multiple classes at once"""
    levels = serializers.ListField(
        child=serializers.CharField(max_length=20),
        help_text="List of levels e.g., ['Primary 1', 'Primary 2']"
    )
    sections = serializers.ListField(
        child=serializers.CharField(max_length=10),
        help_text="List of sections e.g., ['A', 'B', 'C']"
    )
    academic_session = serializers.PrimaryKeyRelatedField(
        queryset=AcademicSession.objects.all()
    )
    max_students = serializers.IntegerField(default=40)

class BulkSubjectCreateSerializer(serializers.Serializer):
    """Serializer for creating multiple subjects at once"""
    subjects = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(max_length=100)
        ),
        help_text="List of subjects with name and optional code"
    )
    
    def validate_subjects(self, value):
        """Validate subjects data structure"""
        for subject in value:
            if 'name' not in subject:
                raise serializers.ValidationError(
                    "Each subject must have a 'name' field"
                )
        return value