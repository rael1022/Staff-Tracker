from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from .models import UserProfile

@receiver(post_save, sender=User)
def create_superuser_profile(sender, instance, created, **kwargs):
    if created and instance.is_superuser:
        UserProfile.objects.create(
            user=instance,
            role="HR",
            is_approved=True,
            department=None
        )

        hr_group, _ = Group.objects.get_or_create(name="HR")
        instance.groups.add(hr_group)

