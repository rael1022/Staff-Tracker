# Create your models here.
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
    assessment_date = models.DateTimeField()
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    stress_level = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Incomplete'
    )
    user_answers = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"PreAssessment - User {self.user.id} - Training {self.training.id} - Score: {self.score}%"
    
    def calculate_score(self):
        if not self.user_answers:
            return 0
        
        questions = AssessmentQuestion.objects.filter(
            training=self.training,
            question_type='pre'
        )
        
        if not questions.exists():
            return 0
        
        total_marks = sum(q.marks for q in questions)
        earned_marks = 0
        
        for question in questions:
            user_answer = self.user_answers.get(str(question.id))
            if user_answer and user_answer.upper() == question.correct_answer:
                earned_marks += question.marks
        
        if total_marks > 0:
            percentage = (earned_marks / total_marks) * 100
            return round(percentage, 2)
        return 0


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
    user_answers = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"PostAssessment - User {self.user.id} - Training {self.training.id} - Score: {self.score}%"
    
    def calculate_score(self):
        if not self.user_answers:
            return 0
        
        questions = AssessmentQuestion.objects.filter(
            training=self.training,
            question_type='post'
        )
        
        if not questions.exists():
            return 0
        
        total_marks = sum(q.marks for q in questions)
        earned_marks = 0
        
        for question in questions:
            user_answer = self.user_answers.get(str(question.id))
            if user_answer and user_answer.upper() == question.correct_answer:
                earned_marks += question.marks
        
        if total_marks > 0:
            percentage = (earned_marks / total_marks) * 100
            return round(percentage, 2)
        return 0