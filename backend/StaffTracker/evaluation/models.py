from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class Evaluation(models.Model):
    RATING_CHOICES = [
        (1, '1 - Very Poor'),
        (2, '2 - Poor'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    ]
    
    evaluation_id = models.AutoField(primary_key=True)
    training = models.ForeignKey(
        'training.Training',
        on_delete=models.CASCADE,
        related_name='evaluations',
        db_column='training_id'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='evaluations',
        db_column='user_id'
    )
    rating = models.IntegerField(choices=RATING_CHOICES)
    feedback = models.TextField(blank=True, null=True)
    evaluation_date = models.DateTimeField(default=timezone.now)
    
    question1_rating = models.IntegerField(
        choices=RATING_CHOICES,
        verbose_name="Overall training organization and structure",
        help_text="1=Very Poor, 5=Excellent"
    )
    question2_rating = models.IntegerField(
        choices=RATING_CHOICES,
        verbose_name="Trainer's knowledge and presentation skills",
        help_text="1=Very Poor, 5=Excellent"
    )
    question3_rating = models.IntegerField(
        choices=RATING_CHOICES,
        verbose_name="Relevance of content to your job",
        help_text="1=Very Poor, 5=Excellent"
    )
    question4_rating = models.IntegerField(
        choices=RATING_CHOICES,
        verbose_name="Quality of training materials and resources",
        help_text="1=Very Poor, 5=Excellent"
    )
    question5_would_recommend = models.BooleanField(
        default=False,
        verbose_name="Would you recommend this training to colleagues?"
    )
    
    class Meta:
        db_table = 'evaluations'
        ordering = ['-evaluation_date']
        constraints = [
            models.UniqueConstraint(
                fields=['training', 'user'],
                name='unique_user_training_evaluation'
            )
        ]
        verbose_name = 'Training Evaluation'
        verbose_name_plural = 'Training Evaluations'
        indexes = [
            models.Index(fields=['training', 'evaluation_date']),
            models.Index(fields=['user', 'evaluation_date']),
        ]
    
    def __str__(self):
        return f"Evaluation #{self.evaluation_id} - {self.training.training_title}"
    
    def get_average_question_rating(self):
        ratings = [
            self.rating,
            self.question1_rating,
            self.question2_rating,
            self.question3_rating,
            self.question4_rating
        ]
        return round(sum(ratings) / len(ratings), 2) if ratings else 0
    
    def get_user_role(self):
        return self.user.role if hasattr(self.user, 'role') else 'Employee'