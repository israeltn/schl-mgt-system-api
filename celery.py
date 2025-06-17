# school_management/celery.py
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')

app = Celery('schl-mgt-system-api')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# apps/results/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from apps.results.models import TermResult
from apps.schools.models import SMTPSettings

@shared_task
def send_result_notification(term_result_id):
    """
    Send email notification to parent when student's result is published
    """
    try:
        term_result = TermResult.objects.get(id=term_result_id)
        student = term_result.student
        school = student.user.school
        
        # Get parent email
        parent_email = None
        if student.parent:
            parent_email = student.parent.email
        elif student.guardian_email:
            parent_email = student.guardian_email
        
        if not parent_email:
            return f"No parent email found for student {student.student_id}"
        
        # Get school SMTP settings
        smtp_settings = SMTPSettings.objects.filter(school=school, is_active=True).first()
        
        if not smtp_settings:
            return f"No SMTP settings configured for school {school.name}"
        
        # Prepare email content
        subject = f"Result Notification - {student.user.get_full_name()} - {term_result.term.name}"
        
        # Email context
        context = {
            'student': student,
            'term_result': term_result,
            'school': school,
            'results': student.results.filter(term=term_result.term)
        }
        
        # Render email templates
        html_message = render_to_string('emails/result_notification.html', context)
        plain_message = render_to_string('emails/result_notification.txt', context)
        
        # Configure email backend with school's SMTP settings
        from django.core.mail import get_connection
        
        connection = get_connection(
            host=smtp_settings.host,
            port=smtp_settings.port,
            username=smtp_settings.username,
            password=smtp_settings.password,
            use_tls=smtp_settings.use_tls,
            use_ssl=smtp_settings.use_ssl,
        )
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=smtp_settings.from_email,
            recipient_list=[parent_email],
            html_message=html_message,
            connection=connection,
            fail_silently=False
        )
        
        return f"Result notification sent to {parent_email} for student {student.student_id}"
        
    except TermResult.DoesNotExist:
        return f"TermResult with id {term_result_id} not found"
    except Exception as e:
        return f"Error sending email: {str(e)}"

@shared_task
def send_fee_reminder(student_id, fee_record_ids):
    """
    Send fee payment reminder to parent/student
    """
    try:
        from apps.students.models import Student
        from apps.financials.models import FeeRecord
        
        student = Student.objects.get(id=student_id)
        fee_records = FeeRecord.objects.filter(id__in=fee_record_ids)
        school = student.user.school
        
        # Get parent email
        parent_email = None
        if student.parent:
            parent_email = student.parent.email
        elif student.guardian_email:
            parent_email = student.guardian_email
        
        if not parent_email:
            return f"No parent email found for student {student.student_id}"
        
        # Get school SMTP settings
        smtp_settings = SMTPSettings.objects.filter(school=school, is_active=True).first()
        
        if not smtp_settings:
            return f"No SMTP settings configured for school {school.name}"
        
        # Calculate total outstanding
        total_outstanding = sum([record.balance for record in fee_records])
        
        # Prepare email content
        subject = f"Fee Payment Reminder - {student.user.get_full_name()}"
        
        context = {
            'student': student,
            'fee_records': fee_records,
            'total_outstanding': total_outstanding,
            'school': school
        }
        
        html_message = render_to_string('emails/fee_reminder.html', context)
        plain_message = render_to_string('emails/fee_reminder.txt', context)
        
        # Configure email backend
        from django.core.mail import get_connection
        
        connection = get_connection(
            host=smtp_settings.host,
            port=smtp_settings.port,
            username=smtp_settings.username,
            password=smtp_settings.password,
            use_tls=smtp_settings.use_tls,
            use_ssl=smtp_settings.use_ssl,
        )
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=smtp_settings.from_email,
            recipient_list=[parent_email],
            html_message=html_message,
            connection=connection,
            fail_silently=False
        )
        
        return f"Fee reminder sent to {parent_email} for student {student.student_id}"
        
    except Student.DoesNotExist:
        return f"Student with id {student_id} not found"
    except Exception as e:
        return f"Error sending fee reminder: {str(e)}"

@shared_task
def bulk_send_result_notifications(term_id, class_id=None):
    """
    Send result notifications to all students in a term/class
    """
    term_results = TermResult.objects.filter(
        term_id=term_id,
        is_published=True
    )
    
    if class_id:
        term_results = term_results.filter(class_for_term_id=class_id)
    
    sent_count = 0
    for term_result in term_results:
        try:
            send_result_notification.delay(term_result.id)
            sent_count += 1
        except Exception as e:
            print(f"Error queuing notification for {term_result.id}: {e}")
    
    return f"Queued {sent_count} result notifications"

# school_management/__init__.py
from .celery import app as celery_app

__all__ = ('celery_app',)