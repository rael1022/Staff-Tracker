from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        role = 'HR' if instance.is_superuser else None
        UserProfile.objects.create(
            user=instance,
            role='HR',
            department=None,
            is_approved=instance.is_superuser
        )

        hr_group, _ = Group.objects.get_or_create(name='HR')
        instance.groups.add(hr_group)