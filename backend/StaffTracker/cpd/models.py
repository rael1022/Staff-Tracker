from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class CPDRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    training = models.ForeignKey("training.Training", on_delete=models.CASCADE)
    points = models.IntegerField()
    earned_date = models.DateField()

    def __str__(self):
        return f"{self.user.username} - {self.points}"