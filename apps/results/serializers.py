from rest_framework import serializers
from .models import Result, TermResult, ResultTemplate

class ResultSerializer(serializers.ModelSerializer):
    """Serializer for Result model"""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    term_name = serializers.CharField(source='term.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    total_score = serializers.ReadOnlyField()
    average_score = serializers.ReadOnlyField()
    grade = serializers.ReadOnlyField()
    grade_point = serializers.ReadOnlyField()
    
    class Meta:
        model = Result
        fields = [
            'id', 'student', 'student_name', 'student_id', 'subject',
            'subject_name', 'term', 'term_name', 'class_for_term',
            'first_ca', 'second_ca', 'exam_marks', 'total_score',
            'average_score', 'grade', 'grade_point', 'remarks',
            'teacher', 'teacher_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ResultInputSerializer(serializers.ModelSerializer):
    """Serializer for inputting/updating results"""
    
    class Meta:
        model = Result
        fields = [
            'student', 'subject', 'term', 'class_for_term',
            'first_ca', 'second_ca', 'exam_marks', 'remarks'
        ]
    
    def validate(self, data):
        """Validate that student is in the specified class"""
        student = data.get('student')
        class_for_term = data.get('class_for_term')
        
        if student.current_class != class_for_term:
            raise serializers.ValidationError(
                "Student is not in the specified class."
            )
        
        return data

class BulkResultInputSerializer(serializers.Serializer):
    """Serializer for bulk result input"""
    class_id = serializers.IntegerField()
    subject_id = serializers.IntegerField()
    term_id = serializers.IntegerField()
    results = serializers.ListField(
        child=serializers.DictField()
    )
    
    def validate_results(self, value):
        """Validate results data structure"""
        for result in value:
            required_fields = ['student_id']
            for field in required_fields:
                if field not in result:
                    raise serializers.ValidationError(
                        f"Each result must have '{field}'"
                    )
        return value

class TermResultSerializer(serializers.ModelSerializer):
    """Serializer for TermResult model"""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    term_name = serializers.CharField(source='term.name', read_only=True)
    class_name = serializers.CharField(source='class_for_term.name', read_only=True)
    subject_results = serializers.SerializerMethodField()
    
    class Meta:
        model = TermResult
        fields = [
            'id', 'student', 'student_name', 'student_id', 'term',
            'term_name', 'class_for_term', 'class_name', 'total_subjects',
            'total_score', 'average_score', 'gpa', 'position',
            'class_teacher_comment', 'principal_comment', 'punctuality',
            'neatness', 'is_published', 'published_at', 'subject_results',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_subject_results(self, obj):
        """Get individual subject results for this term"""
        subject_results = obj.student.results.filter(term=obj.term)
        return ResultSerializer(subject_results, many=True).data

class StudentTermResultSerializer(serializers.ModelSerializer):
    """Simplified serializer for student's own results"""
    term_name = serializers.CharField(source='term.name', read_only=True)
    class_name = serializers.CharField(source='class_for_term.name', read_only=True)
    subject_results = serializers.SerializerMethodField()
    
    class Meta:
        model = TermResult
        fields = [
            'id', 'term_name', 'class_name', 'total_subjects',
            'average_score', 'gpa', 'position', 'subject_results'
        ]
    
    def get_subject_results(self, obj):
        """Get subject results without sensitive information"""
        subject_results = obj.student.results.filter(term=obj.term)
        return [{
            'subject_name': result.subject.name,
            'first_ca': result.first_ca,
            'second_ca': result.second_ca,
            'exam_marks': result.exam_marks,
            'total_score': result.total_score,
            'grade': result.grade
        } for result in subject_results]

class ResultTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ResultTemplate model"""
    
    class Meta:
        model = ResultTemplate
        fields = [
            'id', 'school', 'show_ca_scores', 'show_exam_scores',
            'show_total_scores', 'show_grades', 'show_positions',
            'show_gpa', 'grade_a_min', 'grade_b_min', 'grade_c_min',
            'grade_d_min', 'grade_e_min', 'principal_signature',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ClassResultSummarySerializer(serializers.Serializer):
    """Serializer for class result summary"""
    class_name = serializers.CharField()
    term_name = serializers.CharField()
    total_students = serializers.IntegerField()
    results_published = serializers.IntegerField()
    average_class_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    highest_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    lowest_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    pass_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    
class SubjectPerformanceSerializer(serializers.Serializer):
    """Serializer for subject performance analysis"""
    subject_name = serializers.CharField()
    total_students = serializers.IntegerField()
    average_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    highest_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    lowest_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    grade_distribution = serializers.DictField()