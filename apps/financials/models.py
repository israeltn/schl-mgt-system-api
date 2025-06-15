from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal

class FeeStructure(models.Model):
    """
    Fee structure for different classes and academic sessions
    """
    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='fee_structures'
    )
    academic_session = models.ForeignKey(
        'academics.AcademicSession',
        on_delete=models.CASCADE,
        related_name='fee_structures'
    )
    class_level = models.ForeignKey(
        'academics.Class',
        on_delete=models.CASCADE,
        related_name='fee_structures',
        null=True,
        blank=True
    )
    
    # Fee details
    name = models.CharField(max_length=100)  # e.g., "Tuition Fee", "Development Levy"
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Payment terms
    payment_frequency = models.CharField(
        max_length=20,
        choices=[
            ('termly', 'Termly'),
            ('annual', 'Annual'),
            ('monthly', 'Monthly'),
            ('one_time', 'One Time')
        ],
        default='termly'
    )
    
    # Status
    is_mandatory = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['school', 'academic_session', 'class_level', 'name']
    
    def __str__(self):
        class_info = f" - {self.class_level.name}" if self.class_level else ""
        return f"{self.name} - {self.school.name}{class_info} ({self.academic_session.name})"

class FeeRecord(models.Model):
    """
    Individual fee records for students
    """
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='fee_records'
    )
    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.CASCADE,
        related_name='fee_records'
    )
    term = models.ForeignKey(
        'academics.Term',
        on_delete=models.CASCADE,
        related_name='fee_records',
        null=True,
        blank=True
    )
    
    # Amount details
    amount_due = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('partial', 'Partial Payment'),
            ('cleared', 'Cleared'),
            ('overdue', 'Overdue'),
            ('waived', 'Waived')
        ],
        default='pending'
    )
    
    # Payment details
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('cash', 'Cash'),
            ('bank_transfer', 'Bank Transfer'),
            ('online', 'Online Payment'),
            ('cheque', 'Cheque'),
            ('pos', 'POS')
        ],
        blank=True
    )
    
    # Reference and notes
    payment_reference = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    
    # Who recorded the payment
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recorded_fee_payments',
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.fee_structure.name} - {self.status}"
    
    @property
    def balance(self):
        """Calculate outstanding balance"""
        return self.amount_due - self.amount_paid
    
    @property
    def is_fully_paid(self):
        """Check if fee is fully paid"""
        return self.amount_paid >= self.amount_due
    
    def save(self, *args, **kwargs):
        # Auto-update status based on payment
        if self.amount_paid >= self.amount_due:
            self.status = 'cleared'
        elif self.amount_paid > 0:
            self.status = 'partial'
        else:
            self.status = 'pending'
        
        super().save(*args, **kwargs)

class PaymentHistory(models.Model):
    """
    Track payment history for fee records
    """
    fee_record = models.ForeignKey(
        FeeRecord,
        on_delete=models.CASCADE,
        related_name='payment_history'
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_date = models.DateField()
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('cash', 'Cash'),
            ('bank_transfer', 'Bank Transfer'),
            ('online', 'Online Payment'),
            ('cheque', 'Cheque'),
            ('pos', 'POS')
        ]
    )
    
    payment_reference = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recorded_payments'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.fee_record.student.user.get_full_name()} - {self.amount} - {self.payment_date}"

class Invoice(models.Model):
    """
    Fee invoices for students
    """
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    academic_session = models.ForeignKey(
        'academics.AcademicSession',
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    term = models.ForeignKey(
        'academics.Term',
        on_delete=models.CASCADE,
        related_name='invoices',
        null=True,
        blank=True
    )
    
    # Invoice details
    invoice_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    
    # Amount details
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('sent', 'Sent'),
            ('partial', 'Partial Payment'),
            ('paid', 'Paid'),
            ('overdue', 'Overdue'),
            ('cancelled', 'Cancelled')
        ],
        default='draft'
    )
    
    # Additional information
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_invoices'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.student.user.get_full_name()}"
    
    @property
    def balance(self):
        """Calculate outstanding balance"""
        return self.total_amount - self.amount_paid
    
    def save(self, *args, **kwargs):
        # Auto-generate invoice number if not provided
        if not self.invoice_number:
            school = self.student.user.school
            year = self.issue_date.year
            last_invoice = Invoice.objects.filter(
                student__user__school=school,
                invoice_number__startswith=f"INV{year}"
            ).order_by('invoice_number').last()
            
            if last_invoice:
                last_number = int(last_invoice.invoice_number[-6:])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.invoice_number = f"INV{year}{new_number:06d}"
        
        super().save(*args, **kwargs)

class InvoiceItem(models.Model):
    """
    Individual items in an invoice
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.CASCADE,
        related_name='invoice_items'
    )
    
    description = models.CharField(max_length=200)
    quantity = models.IntegerField(default=1)
    unit_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.description}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate total amount
        self.total_amount = self.quantity * self.unit_amount
        super().save(*args, **kwargs)

class DiscountScheme(models.Model):
    """
    Discount schemes for students (scholarships, siblings discount, etc.)
    """
    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='discount_schemes'
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Discount details
    discount_type = models.CharField(
        max_length=20,
        choices=[
            ('percentage', 'Percentage'),
            ('fixed_amount', 'Fixed Amount')
        ]
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Applicability
    applies_to = models.CharField(
        max_length=20,
        choices=[
            ('all_fees', 'All Fees'),
            ('tuition_only', 'Tuition Only'),
            ('specific_fees', 'Specific Fees')
        ],
        default='all_fees'
    )
    
    # Validity
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.school.name}"

class StudentDiscount(models.Model):
    """
    Discount applications for specific students
    """
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='discounts'
    )
    discount_scheme = models.ForeignKey(
        DiscountScheme,
        on_delete=models.CASCADE,
        related_name='student_discounts'
    )
    academic_session = models.ForeignKey(
        'academics.AcademicSession',
        on_delete=models.CASCADE,
        related_name='student_discounts'
    )
    
    # Application details
    applied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applied_discounts'
    )
    reason = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'discount_scheme', 'academic_session']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.discount_scheme.name}"