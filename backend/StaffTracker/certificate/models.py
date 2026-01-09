from django.db import models
from django.contrib.auth.models import User
from datetime import date
from django.db.models.signals import pre_save
from django.dispatch import receiver

# Create your models here.
class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    training = models.ForeignKey("training.Training", on_delete=models.CASCADE)
    issue_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField()
    trainer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='issued_certificates')
    reminder_soon_sent = models.BooleanField(default=False)
    reminder_expired_sent = models.BooleanField(default=False)

    def is_expired(self):
        return date.today() > self.expiry_date

    def __str__(self):
        return f"{self.user.username} - {self.training}"

@receiver(pre_save, sender=Certificate)
def reset_reminder_flags(sender, instance, **kwargs):
    if instance.pk:  # no new instance
        old_cert = Certificate.objects.get(pk=instance.pk)
        if old_cert.expiry_date != instance.expiry_date:
            # expiry_date changed, reset reminder flags
            instance.reminder_soon_sent = False
            instance.reminder_expired_sent = False