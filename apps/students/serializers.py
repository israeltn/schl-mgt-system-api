from rest_framework import serializers
from django.db.models import Count, Q
from apps.accounts.serializers import UserSerializer
from .models import Student, Enrollment, StudentAttendance

from apps.accounts.models import User
from django.utils import timezone

class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student model"""
    user_details = UserSerializer(source='user', read_only=True)
    age = serializers.ReadOnlyField()
    fee_status = serializers.ReadOnlyField()
    current_class_name = serializers.CharField(source='current_class.name', read_only=True)
    school_name = serializers.CharField(source='user.school.name', read_only=True)
    
    class Meta:
        model = Student
        fields = [
            'id', 'user', 'user_details', 'student_id', 'date_of_birth',
            'gender', 'address', 'emergency_contact', 'blood_group',
            'medical_conditions', 'parent', 'guardian_name', 
            'guardian_relationship', 'guardian_phone', 'guardian_email',
            'admission_date', 'current_class', 'current_class_name',
            'age', 'fee_status', 'school_name', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'student_id', 'created_at']

class StudentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new students"""
    user_data = serializers.DictField(write_only=True)
    
    class Meta:
        model = Student
        fields = [
            'user_data', 'date_of_birth', 'gender', 'address',
            'emergency_contact', 'blood_group', 'medical_conditions',
            'parent', 'guardian_name', 'guardian_relationship',
            'guardian_phone', 'guardian_email', 'admission_date',
            'current_class'
        ]
    
    def create(self, validated_data):
        user_data = validated_data.pop('user_data')
        user_data['role'] = 'student'
        
        # Create the user first
        user = User.objects.create_user(**user_data)
        
        # Create the student profile
        student = Student.objects.create(user=user, **validated_data)
        return student

class StudentCSVImportSerializer(serializers.Serializer):
    """Serializer for CSV import of students"""
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, default='defaultpass123')
    date_of_birth = serializers.DateField()
    gender = serializers.ChoiceField(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    address = serializers.CharField()
    emergency_contact = serializers.CharField(max_length=15)
    blood_group = serializers.CharField(max_length=5, required=False, allow_blank=True)
    medical_conditions = serializers.CharField(required=False, allow_blank=True)
    guardian_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    guardian_relationship = serializers.CharField(max_length=50, required=False, allow_blank=True)
    guardian_phone = serializers.CharField(max_length=15, required=False, allow_blank=True)
    guardian_email = serializers.EmailField(required=False, allow_blank=True)
    admission_date = serializers.DateField()
    current_class = serializers.CharField(max_length=50, required=False, allow_blank=True)

class StudentCSVExportSerializer(serializers.ModelSerializer):
    """Serializer for CSV export of students"""
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.CharField(source='user.email')
    username = serializers.CharField(source='user.username')
    current_class_name = serializers.CharField(source='current_class.name', allow_null=True)
    school_name = serializers.CharField(source='user.school.name')
    
    class Meta:
        model = Student
        fields = [
            'student_id', 'first_name', 'last_name', 'email', 'username',
            'date_of_birth', 'gender', 'address', 'emergency_contact',
            'blood_group', 'medical_conditions', 'guardian_name',
            'guardian_relationship', 'guardian_phone', 'guardian_email',
            'admission_date', 'current_class_name', 'school_name', 'is_active'
        ]

class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for Enrollment model"""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    class_name = serializers.CharField(source='class_enrolled.name', read_only=True)
    session_name = serializers.CharField(source='academic_session.name', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'student', 'student_name', 'student_id',
            'class_enrolled', 'class_name', 'academic_session',
            'session_name', 'enrollment_date', 'is_promoted',
            'promotion_date', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class StudentAttendanceSerializer(serializers.ModelSerializer):
    """Serializer for StudentAttendance model"""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)
    
    class Meta:
        model = StudentAttendance
        fields = [
            'id', 'student', 'student_name', 'student_id', 'date',
            'status', 'time_in', 'time_out', 'remarks',
            'recorded_by', 'recorded_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class BulkAttendanceSerializer(serializers.Serializer):
    """Serializer for bulk attendance recording"""
    date = serializers.DateField()
    class_id = serializers.IntegerField()
    attendance_records = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    
    def validate_attendance_records(self, value):
        """Validate attendance records structure"""
        for record in value:
            if 'student_id' not in record or 'status' not in record:
                raise serializers.ValidationError(
                    "Each attendance record must have 'student_id' and 'status'"
                )
            if record['status'] not in ['present', 'absent', 'late', 'excused']:
                raise serializers.ValidationError(
                    "Status must be one of: present, absent, late, excused"
                )
        return value

class StudentDashboardSerializer(serializers.ModelSerializer):
    """Serializer for student dashboard data"""
    user_details = UserSerializer(source='user', read_only=True)
    current_class_name = serializers.CharField(source='current_class.name', read_only=True)
    school_name = serializers.CharField(source='user.school.name', read_only=True)
    recent_attendance = serializers.SerializerMethodField()
    attendance_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'user_details', 'student_id', 'current_class_name',
            'school_name', 'fee_status', 'recent_attendance',
            'attendance_summary'
        ]
    
    def get_recent_attendance(self, obj):
        """Get recent attendance records"""
        recent_records = obj.attendance_records.order_by('-date')[:5]
        return StudentAttendanceSerializer(recent_records, many=True).data
    
    def get_attendance_summary(self, obj):
        """Get attendance summary for current month"""
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        summary = obj.attendance_records.filter(
            date__month=current_month,
            date__year=current_year
        ).aggregate(
            total_days=Count('id'),
            present_days=Count('id', filter=Q(status='present')),
            absent_days=Count('id', filter=Q(status='absent')),
            late_days=Count('id', filter=Q(status='late'))
        )
        
        return summary