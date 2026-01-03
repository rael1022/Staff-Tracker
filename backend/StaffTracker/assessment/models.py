from django.db import models
from django.contrib.auth.models import User

class AssessmentQuestion(models.Model):
    TYPE_CHOICES = [
        ('pre', 'Pre-Assessment'),
        ('post', 'Post-Assessment'),
    ]
    
    training = models.ForeignKey(
        'training.Training',
        on_delete=models.CASCADE,
        related_name='assessment_questions'
    )
    question_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES
    )
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(
        max_length=1,
        choices=[
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('D', 'D'),
        ]
    )
    marks = models.IntegerField(default=1)
    
    class Meta:
        ordering = ['id']
        unique_together = ['training', 'question_type', 'question_text']
    
    def __str__(self):
        return f"{self.get_question_type_display()} - {self.question_text[:50]}..."

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
    assessment_date = models.DateTimeField(auto_now_add=True)
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    stress_level = models.CharField(max_length=20, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Incomplete'
    )
    
    class Meta:
        unique_together = ['training', 'user']  # 每个用户每个培训只能做一次前测
    
    def __str__(self):
        return f"PreAssessment - {self.user.username} - {self.training.title} - Score: {self.score}%"

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
    assessment_date = models.DateTimeField(auto_now_add=True)
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Incomplete'
    )
    
    class Meta:
        unique_together = ['training', 'user']  # 每个用户每个培训只能做一次后测
    
    def __str__(self):
        return f"PostAssessment - {self.user.username} - {self.training.title} - Score: {self.score}%"