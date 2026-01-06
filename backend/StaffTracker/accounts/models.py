from django.db import models
from django.contrib.auth.models import User
from department.models import Department
from django.core.exceptions import ValidationError

ROLE_CHOICES = (
    ('Employee', 'Employee'),
    ('Trainer', 'Trainer'),
    ('HOD', 'HOD'),
    ('HR', 'HR'),
)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Employee')
    extra_info = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def clean(self):
        if self.role == 'HR' and self.department is not None:
            raise ValidationError("HR should not belong to any department.")

        if self.role in ['Employee', 'Trainer', 'HOD'] and self.department is None:
            raise ValidationError(f"{self.role} must belong to a department.")
    
    def __str__(self):
        return self.user.username
