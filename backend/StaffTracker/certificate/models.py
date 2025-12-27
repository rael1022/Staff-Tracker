from django.db import models
from django.contrib.auth.models import User
from datetime import date

# Create your models here.
class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    training = models.ForeignKey("training.Training", on_delete=models.CASCADE)
    issue_date = models.DateField()
    expiry_date = models.DateField()

    def is_expired(self):
        return date.today() > self.expiry_date

    def __str__(self):
        return f"{self.user.username} - {self.training}"