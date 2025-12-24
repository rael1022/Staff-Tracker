from django.db import models
from django.contrib.auth.models import User

class Training(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=200)
    trainer = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.trainer.username}"

class TrainingRegistration(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')
    ]
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    employee = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'groups__name': 'Employee'})
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.username} -> {self.training.title} ({self.status})"
