import uuid
from django.db import models
from django.conf import settings

class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'Present', 'Present'
        ABSENT = 'Absent', 'Absent'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ABSENT)
    check_in_time = models.DateTimeField(null=True, blank=True)
    date = models.DateField(auto_now_add=True)
        
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='attendances'
    )
    
    training_id = models.CharField(max_length=255)
    
    class Meta:
        db_table = 'attendance'
        unique_together = ['user', 'training_id']
        ordering = ['-date', '-check_in_time'] 
    
    def __str__(self):
        return f"{self.user.username if self.user else 'No user'} - {self.status}"
    
    def save(self, *args, **kwargs):
        if self.user: 
            if Attendance.objects.filter(
                user=self.user, 
                training_id=self.training_id
            ).exclude(id=self.id).exists():
                raise ValueError("The user has checked in for this training.")
        super().save(*args, **kwargs)