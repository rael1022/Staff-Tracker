from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from attendance.models import Attendance
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

class Training(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=200)
    trainer = models.ForeignKey(User, on_delete=models.CASCADE)
    cpd_points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    department = models.ForeignKey(
        'department.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    duration_hours = models.PositiveIntegerField(default=1)  

    def __str__(self):
        return f"{self.title} by {self.trainer.username}"
    
    def mark_absent_for_unchecked_users(self):
        current_time = timezone.now()
        training_end_time = datetime.combine(
            self.date, 
            self.time
        ).replace(tzinfo=current_time.tzinfo) + timedelta(hours=self.duration_hours)
        
        if current_time < training_end_time:
            return 0, "Training has not ended yet"
        
        marked_count = 0
        
        try:
            approved_registrations = self.trainingregistration_set.filter(
                status='Approved'
            )
            
            for registration in approved_registrations:
                user = registration.employee
                
                existing_attendance = Attendance.objects.filter(
                    user=user,
                    training_id=str(self.id)
                ).first()
                
                if not existing_attendance:
                    Attendance.objects.create(
                        user=user,
                        training_id=str(self.id),
                        status=Attendance.Status.ABSENT,
                        check_in_time=None,
                        date=self.date
                    )
                    marked_count += 1
                    
                    if registration.complete_status == 'Not Completed':
                        registration.complete_status = 'Completed'
                        registration.save()
                
            return marked_count, f"Marked {marked_count} users as absent"
                
        except Exception as e:
            return 0, f"Error: {str(e)}"
    
    def get_registered_users_without_attendance(self):
        from attendance.models import Attendance
        
        registered_users = []
        approved_registrations = self.trainingregistration_set.filter(status='Approved')
        
        for registration in approved_registrations:
            user = registration.employee
            
            existing_attendance = Attendance.objects.filter(
                user=user,
                training_id=str(self.id)
            ).first()
            
            if not existing_attendance:
                registered_users.append({
                    'user': user,
                    'registration': registration
                })
        
        return registered_users

class TrainingRegistration(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')
    ]
    
    COMPLETE_CHOICES = [
        ('Not Completed', 'Not Completed'),
        ('Completed', 'Completed'),
    ]
    
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'groups__name': 'Employee'}
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    complete_status = models.CharField(
        max_length=15,
        choices=COMPLETE_CHOICES,
        default='Not Completed'
    )
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.username} -> {self.training.title} ({self.status}, {self.complete_status})"