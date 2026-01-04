from django.db import models
from django.contrib.auth.models import User
from department.models import Department

ROLE_CHOICES = (
    ('Employee', 'Employee'),
    ('Trainer', 'Trainer'),
    ('HOD', 'HOD'),
)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    extra_info = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    def __str__(self):
        return self.user.username
