from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Result(models.Model):
    """
    Student results for subjects in specific terms
    """
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='results'
    )
    subject = models.ForeignKey(
        'academics.Subject',
        on_delete=models.CASCADE,
        related_name='results'
    )
    term = models.ForeignKey(
        'academics.Term',
        on_delete=models.CASCADE,
        related_name='results'
    )
    class_for_term = models.ForeignKey(
        'academics.Class',
        on_delete=models.CASCADE,
        related_name='term_results'
    )
    
    # Assessment scores (out of 100)
    first_ca = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True,
        verbose_name="First Continuous Assessment"
    )
    second_ca = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True,
        verbose_name="Second Continuous Assessment"
    )
    exam_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True,
        verbose_name="Examination Marks"
    )
    
    # Additional fields
    remarks = models.TextField(blank=True)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_results',
        limit_choices_to={'role': 'teacher'}
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'subject', 'term']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.subject.name} - {self.term.name}"
    
    @property
    def total_score(self):
        """Calculate total score from all assessments"""
        scores = [self.first_ca, self.second_ca, self.exam_marks]
        valid_scores = [score for score in scores if score is not None]
        return sum(valid_scores) if valid_scores else 0
    
    @property
    def average_score(self):
        """Calculate average score"""
        scores = [self.first_ca, self.second_ca, self.exam_marks]
        valid_scores = [score for score in scores if score is not None]
        return sum(valid_scores) / len(valid_scores) if valid_scores else 0
    
    @property
    def grade(self):
        """Calculate grade based on average score"""
        avg = self.average_score
        if avg >= 80:
            return 'A'
        elif avg >= 70:
            return 'B'
        elif avg >= 60:
            return 'C'
        elif avg >= 50:
            return 'D'
        elif avg >= 40:
            return 'E'
        else:
            return 'F'
    
    @property
    def grade_point(self):
        """Get grade point based on grade"""
        grade_points = {
            'A': 5.0, 'B': 4.0, 'C': 3.0,
            'D': 2.0, 'E': 1.0, 'F': 0.0
        }
        return grade_points.get(self.grade, 0.0)

class TermResult(models.Model):
    """
    Aggregated term results for a student
    """
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='term_results'
    )
    term = models.ForeignKey(
        'academics.Term',
        on_delete=models.CASCADE,
        related_name='student_results'
    )
    class_for_term = models.ForeignKey(
        'academics.Class',
        on_delete=models.CASCADE,
        related_name='class_term_results'
    )
    
    # Calculated fields
    total_subjects = models.IntegerField(default=0)
    total_score = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gpa = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    
    # Position in class
    position = models.IntegerField(null=True, blank=True)
    
    # Comments
    class_teacher_comment = models.TextField(blank=True)
    principal_comment = models.TextField(blank=True)
    
    # Behavioral assessments
    punctuality = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('very_good', 'Very Good'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor')
        ],
        blank=True
    )
    neatness = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('very_good', 'Very Good'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor')
        ],
        blank=True
    )
    
    # Status
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'term']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.term.name} Result"
    
    def calculate_results(self):
        """Calculate aggregated results from individual subject results"""
        subject_results = self.student.results.filter(term=self.term)
        
        if not subject_results.exists():
            return
        
        total_score = sum([result.average_score for result in subject_results])
        total_subjects = subject_results.count()
        total_grade_points = sum([result.grade_point for result in subject_results])
        
        self.total_subjects = total_subjects
        self.total_score = total_score
        self.average_score = total_score / total_subjects if total_subjects > 0 else 0
        self.gpa = total_grade_points / total_subjects if total_subjects > 0 else 0
        self.save()
    
    def calculate_position(self):
        """Calculate position in class based on average score"""
        class_results = TermResult.objects.filter(
            term=self.term,
            class_for_term=self.class_for_term
        ).order_by('-average_score')
        
        for position, result in enumerate(class_results, 1):
            result.position = position
            result.save(update_fields=['position'])

class ResultTemplate(models.Model):
    """
    Template for result sheet customization per school
    """
    school = models.OneToOneField(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='result_template'
    )
    
    # Template settings
    show_ca_scores = models.BooleanField(default=True)
    show_exam_scores = models.BooleanField(default=True)
    show_total_scores = models.BooleanField(default=True)
    show_grades = models.BooleanField(default=True)
    show_positions = models.BooleanField(default=True)
    show_gpa = models.BooleanField(default=True)
    
    # Grading system
    grade_a_min = models.IntegerField(default=80)
    grade_b_min = models.IntegerField(default=70)
    grade_c_min = models.IntegerField(default=60)
    grade_d_min = models.IntegerField(default=50)
    grade_e_min = models.IntegerField(default=40)
    
    # Comments template
    principal_signature = models.ImageField(
        upload_to='signatures/',
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Result Template - {self.school.name}"