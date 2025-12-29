# Create your models here.
from django.db import models
from django.contrib.auth.models import User


class PreAssessment(models.Model):
    STATUS_CHOICES = [
        ('Completed', 'Completed'),
        ('Incomplete', 'Incomplete'),
    ]
    
    training = models.ForeignKey(
        'training.Training',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    assessment_date = models.DateTimeField()
    score = models.IntegerField()
    stress_level = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Incomplete'
    )

    def __str__(self):
        return f"PreAssessment - User {self.user.id} - Training {self.training.id}"


class PostAssessment(models.Model):
    STATUS_CHOICES = [
        ('Completed', 'Completed'),
        ('Incomplete', 'Incomplete'),
    ]
    
    training = models.ForeignKey(
        'training.Training',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    assessment_date = models.DateTimeField()
    score = models.IntegerField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Incomplete'
    )

    def __str__(self):
        return f"PostAssessment - User {self.user.id} - Training {self.training.id}"
